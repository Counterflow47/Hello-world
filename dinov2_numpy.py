import numpy as np
from scipy.ndimage import zoom


def gelu(x):
    # tanh-approx GELU (same as many transformer impls)
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))))


def softmax(x, axis=-1):
    x_max = np.max(x, axis=axis, keepdims=True)
    x_exp = np.exp(x - x_max)
    x_sum = np.sum(x_exp, axis=axis, keepdims=True)
    return x_exp / x_sum


class Embeddings:
    def __init__(self, weights):
        """
        NumPy 实现的 Dinov2 Embeddings 层。

        weights 包含：
          - embeddings.cls_token: (1, 1, D)
          - embeddings.position_embeddings: (1, N+1, D)
          - embeddings.patch_embeddings.projection.weight: (D, C, ps, ps) 或等价形状
          - embeddings.patch_embeddings.projection.bias: (D,)
        """
        self.hidden_size = 768  # D
        self.patch_size = 14    # ps

        self.cls_token = weights["embeddings.cls_token"]  # (1, 1, D)
        self.position_embeddings = weights["embeddings.position_embeddings"]  # (1, N+1, D)

        # patch projection weight: (D, C, ps, ps) -> (D, C*ps*ps) -> transpose -> (C*ps*ps, D)
        proj_w = weights["embeddings.patch_embeddings.projection.weight"]
        self.patch_embed_w = proj_w.reshape(self.hidden_size, -1).T  # (patch_dim, D)

        proj_b = weights["embeddings.patch_embeddings.projection.bias"]
        self.patch_embed_b = proj_b.reshape(self.hidden_size, 1).T   # (1, D)

    def pixel2patches(self, pixel_values):
        B, C, H, W = pixel_values.shape
        ps = self.patch_size
        assert H % ps == 0 and W % ps == 0, f"H,W must be divisible by patch_size={ps}, got {(H, W)}"

        patches = []
        for i in range(0, H, ps):
            for j in range(0, W, ps):
                patch = pixel_values[:, :, i:i+ps, j:j+ps].reshape(B, -1)  # (B, C*ps*ps)
                patches.append(patch)

        patches = np.stack(patches, axis=1)  # (B, num_patches, patch_dim)
        return patches

    def interpolate_pos_encoding(self, embeddings, height, width):
        """
        将 self.position_embeddings (训练时固定网格) 插值到当前输入分辨率对应的 patch 网格。

        返回形状：(1, 1 + new_num_patches, D)，可广播到 batch 维。
        """
        ps = self.patch_size
        new_h = height // ps
        new_w = width // ps
        new_num_patches = new_h * new_w

        pos = self.position_embeddings  # (1, 1+old_num_patches, D)
        old_num_patches = pos.shape[1] - 1
        D = pos.shape[2]

        # 如果 patch 数完全一致，直接返回
        if old_num_patches == new_num_patches:
            return pos

        # 分离 cls 与 patch 位置编码
        cls_pos = pos[:, :1, :]         # (1, 1, D)
        patch_pos = pos[:, 1:, :]       # (1, old_num_patches, D)

        # 旧网格尺寸（一般为 sqrt(old_num_patches) x sqrt(old_num_patches)）
        old_size = int(np.sqrt(old_num_patches))
        if old_size * old_size != old_num_patches:
            raise ValueError(
                f"old_num_patches={old_num_patches} is not a perfect square; "
                "cannot infer 2D grid for position embedding interpolation."
            )

        # (1, old_num_patches, D) -> (1, old_h, old_w, D)
        patch_pos_2d = patch_pos.reshape(1, old_size, old_size, D)

        # SciPy zoom：对 (H, W) 维度缩放到 (new_h, new_w)
        zoom_h = new_h / old_size
        zoom_w = new_w / old_size

        # order=3 ~ bicubic（更接近很多 ViT 实现），你也可以改成 1 更稳更快
        patch_pos_2d_resized = zoom(
            patch_pos_2d,
            zoom=(1.0, zoom_h, zoom_w, 1.0),
            order=3
        )

        # (1, new_h, new_w, D) -> (1, new_num_patches, D)
        patch_pos_resized = patch_pos_2d_resized.reshape(1, new_num_patches, D)

        # 拼回 cls + patch
        return np.concatenate([cls_pos, patch_pos_resized], axis=1)  # (1, 1+new_num_patches, D)

    def __call__(self, pixel_values):
        B, _, H, W = pixel_values.shape

        patch_values = self.pixel2patches(pixel_values)  # (B, h*w, C*ps*ps)

        # (B, h*w, patch_dim) @ (patch_dim, D) + (1, D) -> (B, h*w, D)
        embeddings = patch_values @ self.patch_embed_w + self.patch_embed_b

        cls_token = np.tile(self.cls_token, (B, 1, 1))  # (B, 1, D)
        embeddings = np.concatenate([cls_token, embeddings], axis=1)  # (B, 1+h*w, D)

        pos_embed = self.interpolate_pos_encoding(embeddings, H, W)  # (1, 1+h*w, D) or same length
        embeddings = embeddings + pos_embed  # broadcast on batch
        return embeddings


class LayerNorm:
    def __init__(self, weight, bias, eps=1e-6):
        self.weight = weight
        self.bias = bias
        self.eps = eps

    def __call__(self, x):
        mean = x.mean(-1, keepdims=True)
        var = x.var(-1, keepdims=True)
        norm = (x - mean) / np.sqrt(var + self.eps)
        return norm * self.weight + self.bias


class LayerScale:
    def __init__(self, lambda1):
        self.lambda1 = lambda1

    def __call__(self, x):
        return x * self.lambda1


class Linear:
    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias

    def __call__(self, x):
        # x: (..., in_features), weight: (out_features, in_features)
        return x @ self.weight.T + self.bias


class SingleHeadAttention:
    def __init__(self, config, prefix, weights):
        self.hidden_size = config["hidden_size"]

        q_w = weights[f"{prefix}.attention.query.weight"]
        q_b = weights[f"{prefix}.attention.query.bias"]
        k_w = weights[f"{prefix}.attention.key.weight"]
        k_b = weights[f"{prefix}.attention.key.bias"]
        v_w = weights[f"{prefix}.attention.value.weight"]
        v_b = weights[f"{prefix}.attention.value.bias"]
        o_w = weights[f"{prefix}.output.dense.weight"]
        o_b = weights[f"{prefix}.output.dense.bias"]

        self.q_proj = Linear(q_w, q_b)
        self.k_proj = Linear(k_w, k_b)
        self.v_proj = Linear(v_w, v_b)
        self.out_proj = Linear(o_w, o_b)

    def __call__(self, x):
        q = self.q_proj(x)  # (B, N, D)
        k = self.k_proj(x)  # (B, N, D)
        v = self.v_proj(x)  # (B, N, D)

        att = np.matmul(q, k.transpose(0, 2, 1)) / np.sqrt(self.hidden_size)  # (B, N, N)
        att = softmax(att, axis=-1)
        out = np.matmul(att, v)  # (B, N, D)
        return self.out_proj(out)


class MultiHeadAttention:
    def __init__(self, config, prefix, weights):
        self.hidden_size = config["hidden_size"]
        self.num_heads = config["num_heads"]
        assert self.hidden_size % self.num_heads == 0, "hidden_size must be divisible by num_heads"
        self.head_dim = self.hidden_size // self.num_heads

        q_w = weights[f"{prefix}.attention.query.weight"]
        q_b = weights[f"{prefix}.attention.query.bias"]
        k_w = weights[f"{prefix}.attention.key.weight"]
        k_b = weights[f"{prefix}.attention.key.bias"]
        v_w = weights[f"{prefix}.attention.value.weight"]
        v_b = weights[f"{prefix}.attention.value.bias"]
        o_w = weights[f"{prefix}.output.dense.weight"]
        o_b = weights[f"{prefix}.output.dense.bias"]

        self.q_proj = Linear(q_w, q_b)
        self.k_proj = Linear(k_w, k_b)
        self.v_proj = Linear(v_w, v_b)
        self.out_proj = Linear(o_w, o_b)

    def __call__(self, x):
        """
        x: (B, N, D)
        return: (B, N, D)
        """
        B, N, D = x.shape
        H = self.num_heads
        d = self.head_dim

        q = self.q_proj(x)  # (B, N, D)
        k = self.k_proj(x)  # (B, N, D)
        v = self.v_proj(x)  # (B, N, D)

        # (B, N, D) -> (B, H, N, d)
        q = q.reshape(B, N, H, d).transpose(0, 2, 1, 3)
        k = k.reshape(B, N, H, d).transpose(0, 2, 1, 3)
        v = v.reshape(B, N, H, d).transpose(0, 2, 1, 3)

        # attention: (B, H, N, N)
        att = np.matmul(q, k.transpose(0, 1, 3, 2)) / np.sqrt(d)
        att = softmax(att, axis=-1)

        # out: (B, H, N, d)
        out = np.matmul(att, v)

        # (B, H, N, d) -> (B, N, D)
        out = out.transpose(0, 2, 1, 3).reshape(B, N, D)

        return self.out_proj(out)


class MLP:
    def __init__(self, prefix, weights):
        w1 = weights[f"{prefix}.mlp.fc1.weight"]
        b1 = weights[f"{prefix}.mlp.fc1.bias"]
        w2 = weights[f"{prefix}.mlp.fc2.weight"]
        b2 = weights[f"{prefix}.mlp.fc2.bias"]

        self.fc1 = Linear(w1, b1)
        self.fc2 = Linear(w2, b2)

    def __call__(self, x):
        return self.fc2(gelu(self.fc1(x)))


class TransformerBlock:
    def __init__(self, config, idx, weights):
        prefix = f"encoder.layer.{idx}"

        self.norm1 = LayerNorm(weights[f"{prefix}.norm1.weight"], weights[f"{prefix}.norm1.bias"])
        self.scale1 = LayerScale(weights[f"{prefix}.layer_scale1.lambda1"])
        self.attn = MultiHeadAttention(config, f"{prefix}.attention", weights)

        self.norm2 = LayerNorm(weights[f"{prefix}.norm2.weight"], weights[f"{prefix}.norm2.bias"])
        self.scale2 = LayerScale(weights[f"{prefix}.layer_scale2.lambda1"])
        self.mlp = MLP(f"{prefix}", weights)

    def __call__(self, x):
        x = x + self.scale1(self.attn(self.norm1(x)))
        x = x + self.scale2(self.mlp(self.norm2(x)))
        return x


class Dinov2Numpy:
    def __init__(self, weights, config=None):
        self.weights = weights
        self.config = config or {
            "hidden_size": 768,
            "num_heads": 12,
            "num_layers": 12,
            "patch_size": 14,
        }

        self.embeddings = Embeddings(weights)
        self.blocks = [TransformerBlock(self.config, i, weights) for i in range(self.config["num_layers"])]
        self.norm = LayerNorm(weights["layernorm.weight"], weights["layernorm.bias"])

    def __call__(self, pixel_values):
        x = self.embeddings(pixel_values)  # (B, 1+num_patches, D)
        for blk in self.blocks:
            x = blk(x)
        x = self.norm(x)
        return x[:, 0]  # CLS: (B, D)
