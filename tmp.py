import numpy as np
from collections import defaultdict

# Sample data from your steel_grade_production table
data = [
        (1, '2024-06-01', 'Rebar', 'B500A', 8724.0),
(2, '2024-07-01', 'Rebar', 'B500A', 9230.0),
(3, '2024-08-01', 'Rebar', 'B500A', 8989.0),
(4, '2024-06-01', 'Rebar', 'B500B', 10880.0),
(5, '2024-07-01', 'Rebar', 'B500B', 11030.0),
(6, '2024-08-01', 'Rebar', 'B500B', 10822.0),
(7, '2024-06-01', 'Rebar', 'B500C', 4111.0),
(8, '2024-07-01', 'Rebar', 'B500C', 1557.0),
(9, '2024-08-01', 'Rebar', 'B500C', 4756.0),
(10, '2024-06-01', 'MBQ', 'A36', 0.0),
(11, '2024-07-01', 'MBQ', 'A36', 202.0),
(12, '2024-08-01', 'MBQ', 'A36', 199.0),
(13, '2024-06-01', 'MBQ', 'A5888', 512.0),
(14, '2024-07-01', 'MBQ', 'A5888', 0.0),
(15, '2024-08-01', 'MBQ', 'A5888', 0.0),
(16, '2024-06-01', 'MBQ', 'GR50', 935.0),
(17, '2024-07-01', 'MBQ', 'GR50', 0.0),
(18, '2024-08-01', 'MBQ', 'GR50', 0.0),
(19, '2024-06-01', 'MBQ', '44W', 0.0),
(20, '2024-07-01', 'MBQ', '44W', 3204.0),
(21, '2024-08-01', 'MBQ', '44W', 3112.0),
(22, '2024-06-01', 'MBQ', '50W', 0.0),
(23, '2024-07-01', 'MBQ', '50W', 3199.0),
(24, '2024-08-01', 'MBQ', '50W', 2879.0),
(25, '2024-06-01', 'MBQ', '55W', 333.0),
(26, '2024-07-01', 'MBQ', '55W', 0.0),
(27, '2024-08-01', 'MBQ', '55W', 0.0),
(28, '2024-06-01', 'MBQ', '60W', 0.0),
(29, '2024-07-01', 'MBQ', '60W', 0.0),
(30, '2024-08-01', 'MBQ', '60W', 0.0),
(31, '2024-06-01', 'SBQ', 'S235JR', 99.0),
(32, '2024-07-01', 'SBQ', 'S235JR', 0.0),
(33, '2024-08-01', 'SBQ', 'S235JR', 0.0),
(34, '2024-06-01', 'SBQ', 'S355J', 102.0),
(35, '2024-07-01', 'SBQ', 'S355J', 0.0),
(36, '2024-08-01', 'SBQ', 'S355J', 0.0),
(37, '2024-06-01', 'SBQ', 'C35', 0.0),
(38, '2024-07-01', 'SBQ', 'C35', 0.0),
(39, '2024-08-01', 'SBQ', 'C35', 0.0),
(40, '2024-06-01', 'SBQ', 'C40', 612.0),
(41, '2024-07-01', 'SBQ', 'C40', 601.0),
(42, '2024-08-01', 'SBQ', 'C40', 603.0),
(43, '2024-06-01', 'CHQ', 'A53/A543', 2078.0),
(44, '2024-07-01', 'CHQ', 'A53/A543', 1032.0),
(45, '2024-08-01', 'CHQ', 'A53/A543', 0.0),
(46, '2024-06-01', 'CHQ', 'A53/C591', 308.0),
(47, '2024-07-01', 'CHQ', 'A53/C591', 0.0),
(48, '2024-08-01', 'CHQ', 'A53/C591', 2541.0)
]

# Create a dictionary to hold arrays for each quality
quality_arrays = {}

# Populate the dictionary
for record in data:
    quality = record[2]
    production = record[4]
    
    if quality not in quality_arrays:
        quality_arrays[quality] = []
    
    quality_arrays[quality].append(production)

# Convert lists to NumPy arrays
for quality in quality_arrays:
    quality_arrays[quality] = np.array(quality_arrays[quality]).reshape(-1, 3)  # Adjust shape as needed

# Example of accessing the arrays
print(quality_arrays)
