import numpy as np

from dinov2_numpy import Dinov2Numpy
from preprocess_image import center_crop

def main():
    weights = np.load("vit-dinov2-base.npz")
    vit = Dinov2Numpy(weights)

    cat_pixel_values = center_crop("./demo_data/cat.jpg")
    cat_feat = vit(cat_pixel_values)  # (1, 768)

    dog_pixel_values = center_crop("./demo_data/dog.jpg")
    dog_feat = vit(dog_pixel_values)  # (1, 768)

    # (2, 768)
    feats = np.concatenate([cat_feat, dog_feat], axis=0)

    # reference: expected features
    ref = np.load("./demo_data/cat_dog_feature.npy")  # usually (2, 768)

    # compare
    diff = feats - ref
    max_abs = np.max(np.abs(diff))
    mean_abs = np.mean(np.abs(diff))
    l2 = np.linalg.norm(diff)

    print("feats shape:", feats.shape, "ref shape:", ref.shape)
    print("max_abs_diff:", float(max_abs))
    print("mean_abs_diff:", float(mean_abs))
    print("l2_diff:", float(l2))

    # typical tolerance (float32 / numpy impl): adjust if needed
    tol = 1e-4
    if max_abs < tol:
        print(f"[OK] within tolerance {tol}")
    else:
        print(f"[WARN] NOT within tolerance {tol}")

if __name__ == "__main__":
    main()
