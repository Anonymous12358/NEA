import itertools
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


class Board:
    @dataclass
    class Line:
        tiles: Sequence[int]
        tile_indices: Sequence[tuple[int, ...]]
        center: int

    def __init__(self, dimensions: tuple[int, ...]):
        self.__data = np.zeros(dimensions, dtype='int8')

    def get_node(self, coords: tuple[int, ...]) -> int:
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        return self.__data[coords]

    def remove(self, coords: tuple[int, ...]):
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        self.__data[coords] = 0

    def place(self, coords: tuple[int, ...], color: int):
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")
        if color <= 0:
            raise ValueError(f"Invalid color {color} should be greater than 0")
        self.__data[coords] = color

    def get_lines(self, coords: tuple[int, ...]) -> list[Line]:
        """
        Get all lines, orthogonal or diagonal in any number of dimensions, through a given center
        :param coords: The coordinates of the center
        :returns: A list of tuples of the index of the center in each line, and the line itself
        """
        
        if len(coords) != self.__data.ndim:
            raise ValueError("Must provide a number of coordinates equal to the number of dimensions of the board")

        # Create an array of indexes so we can tell where the returned tiles came from
        # The 0th dimension ranges over dimensions of the board
        # Named iarray to aid the reader in resolving variable names
        iarray = np.indices(self.__data.shape)

        result = []

        for directs_num in range(3 ** len(coords)):
            # The direction in which this line travels in each dimension
            # directs_num // 3**i % 3 extracts the ith digit of directs_num in ternary
            directs = tuple(directs_num // 3 ** i % 3 - 1 for i in range(len(coords)))
            # No line travels through 0 dimensions
            if all(direction == 0 for direction in directs):
                continue

            # Transform the array so that the line travels forward in all dimensions in which it travels
            # We perform operations on iarray and then use those to index the board in order to get the tiles
            # Start with a slice(None) to skip the 0th dimension of iarray
            transform_indices = [slice(None)]
            for ordinate, direction in zip(coords, directs):
                if direction == -1:
                    transform_indices.append(slice(None, None, -1))
                else:
                    transform_indices.append(slice(None))
            transformed_iarrray = iarray[tuple(transform_indices)]

            # Transform coords so that they are coords into the transformed array
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
            crop_indices = [slice(None)]
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

            cropped_iarray = transformed_iarrray[tuple(crop_indices)]

            # Take the diagonal from iarray for each dimension, and combine into a tuple
            # np.einsum can get a diagonal in an arbitrary number of dimensions
            tile_indices = tuple(
                np.einsum(f'{"i"*(cropped_iarray.ndim-1)}->i', dimension)
                for dimension in cropped_iarray
            )

            # Make tiles a copy so that operations on it can't alter the board
            tiles = np.copy(self.__data[tile_indices])

            # Convert tile_indices from a tuple of arrays to an array of tuples, since the latter is more useful
            # elsewhere in the program
            result.append(Board.Line(tiles, list(zip(*tile_indices)), min_ordinate))

        return result
