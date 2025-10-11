import os

import tensorflow as tf


# Suppress TensorFlow INFO and WARNING messages
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


print("--- TensorFlow Basic Test ---")

# 1. Print TensorFlow Version
try:
    print(f"TensorFlow Version: {tf.__version__}")
except Exception as e:
    print(f"Error getting TensorFlow version: {e}")
    exit()

# 2. Create and manipulate a simple tensor
try:
    # Create two constant tensors
    a = tf.constant([1.0, 2.0, 3.0], name="a")
    b = tf.constant([4.0, 5.0, 6.0], name="b")

    # Perform a basic operation
    c = a + b

    print(f"Tensor 'a': {a.numpy()}")
    print(f"Tensor 'b': {b.numpy()}")
    print(f"Result of 'a + b': {c.numpy()}")
    print("\nSUCCESS: TensorFlow is installed and working correctly.")

except Exception as e:
    print(f"\nERROR: An error occurred during a basic TensorFlow operation: {e}")

print("--- Test Complete ---")
