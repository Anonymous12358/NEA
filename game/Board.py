import itertools
import numpy as np
from typing import Tuple, List


class Board:
    def __init__(self, dimensions: Tuple[int, ...]):
        self.__data = np.zeros(dimensions, dtype='int8')

    def get_node(self, coords: Tuple[int, ...]) -> int:
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        return self.__data[coords]

    def remove(self, coords: Tuple[int, ...]):
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        self.__data[coords] = 0

    def place(self, coords: Tuple[int, ...], color: int):
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        if color <= 0:
            raise ValueError(f"Invalid color {color} should be greater than 0")
        self.__data[coords] = color

    def get_lines(self, coords: Tuple[int, ...]) -> List[Tuple[int, np.ndarray]]:
        """
        Get all lines, orthogonal or diagonal in any number of dimensions, through a given center
        :param coords: The coordinates of the center
        :returns: A list of tuples of the index of the center in each line, and the line itself
        """

        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")

        result = []

        for directs_num in range(3 ** len(coords)):
            # The direction in which this line travels in each dimension
            # directs_num // 3**i % 3 extracts the ith digit of directs_num in ternary
            directs = [directs_num // 3 ** i % 3 - 1 for i in range(len(coords))]
            # No line travels through 0 dimensions
            if all(direction == 0 for direction in directs):
                continue

            # Transform the array so that the line travels forward in all dimensions in which it travels
            transform_indices = []
            for ordinate, direction in zip(coords, directs):
                if direction == -1:
                    transform_indices.append(slice(None, None, -1))
                else:
                    transform_indices.append(slice(None))
            transformed = self.__data[tuple(transform_indices)]

            # Transform coords so that they are coords into transformed
            transformed_coords = tuple(
                length-1 - ordinate if direction == -1 else ordinate
                for length, ordinate, direction in zip(self.__data.shape, coords, directs)
            )

            # end_distances are the distances from the center to the end of the transformed array in each dimension
            end_distances = [length-1 - ordinate for length, ordinate in zip(self.__data.shape, transformed_coords)]

            # The position of the center in the line is the minimum ordinate for a dimension in which the line travels
            min_ordinate = min(itertools.compress(transformed_coords, [direction != 0 for direction in directs]))
            min_end_distance = min(itertools.compress(end_distances, [direction != 0 for direction in directs]))

            # Crop the array so that the main diagonal passes through the desired center
            # To achieve this, the center must have the same distance from the start in every dimension
            # It must also have the same distance from the end so that the array is the same length in every dimension
            # We also crop out the dimensions in which the line doesn't travel at this stage
            crop_indices = []
            for ordinate, end_distance, direction in zip(transformed_coords, end_distances, directs):
                if direction == 0:
                    # In this dimension, we only want the index that contains the center
                    crop_indices.append(ordinate)
                else:
                    # Crop so that the distance from the start to the centre in each dimension is the same
                    # ie each ordinate of the center within the cropped array is the same as min(transformed_coords)
                    start_index = ordinate - min_ordinate

                    # Crop so that the distance from the center to the end in each dimension is the same
                    # `or None` ensures that we cut to the end, rather than the start, if the returned value is 0
                    end_index = -(end_distance - min_end_distance) or None

                    crop_indices.append(slice(start_index, end_index))

            cropped = transformed[tuple(crop_indices)]

            # np.einsum can get a diagonal in an arbitrary number of dimensions
            line = np.einsum(f'{"i"*cropped.ndim}->i', cropped)
            # The returned line is a writeable view, so copy it so that operations on it can't alter the board
            result.append((min_ordinate, np.copy(line)))

        return result
