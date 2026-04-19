import cv2
import numpy as np
from scipy.stats import entropy

def calculate_entropy(image_path):
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.flatten()
    hist = hist[hist > 0]

    prob = hist / hist.sum()
    entropia = -np.sum(prob * np.log2(prob))

    return entropia, gray

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python entropy_image.py <imagen>")
        sys.exit(1)

    entropia, img = calculate_entropy(sys.argv[1])
    print(f"Entropía: {entropia:.4f} bits")
    print(f"Dimensiones: {img.shape}")
    print(f"Rango valores: [{img.min()}, {img.max()}]")
