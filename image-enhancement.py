import cv2
import numpy as np

# Load the image
image_path = '/Users/sebasqui/Documents/Personal/projects/WordleBrad/new_wordle_31_may_2.png'
image = cv2.imread(image_path)

# Define the color ranges
# Aqua Forest (approx. green)
aqua_forest_lower = np.array([40, 50, 50])
aqua_forest_upper = np.array([80, 255, 255])

# Goldenrod (approx. yellow)
goldenrod_lower = np.array([20, 100, 100])
goldenrod_upper = np.array([30, 255, 255])

# Convert image to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Create masks for the color ranges
aqua_forest_mask = cv2.inRange(hsv_image, aqua_forest_lower, aqua_forest_upper)
goldenrod_mask = cv2.inRange(hsv_image, goldenrod_lower, goldenrod_upper)

# Define the new colors in BGR (OpenCV uses BGR by default)
new_green = np.array([0, 255, 0])  # Green
new_yellow = np.array([0, 255, 255])  # Yellow

# Change colors in the original image
image[aqua_forest_mask > 0] = new_green
image[goldenrod_mask > 0] = new_yellow

# Save the modified image
output_path = '/Users/sebasqui/Documents/Personal/projects/WordleBrad/new_wordle_31_may_2_improved.png'
cv2.imwrite(output_path, image)

# Display the modified image (optional)
# cv2.imshow('Modified Image', image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

output_path
