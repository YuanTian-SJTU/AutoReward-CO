"""
Repositories for solving the task allocation problem.
"""
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
from math import sqrt, radians
import copy
import dataset


@funsearch.evolve
# def priority(sorted_combinations: dict) -> tuple[int, int, int]:
#     """
#     Generate a priority function to select and remove the highest priority task combination from the sorted combinations dictionary. Task priority should be dynamically assessed based on the following criteria:

#     1. Prefer tasks covering the largest number of previously uncovered points.
#     2. If tasks cover an equal number of points, select the task with the least overlap with already covered points.
#     3. If multiple tasks still remain, choose the task with the smallest index number.

#     Args:
#         sorted_combinations (dict): Sorted combinations of tasks.
#             - Key (tuple[int, int, int]): Contains satellite index, pass index, and task index in the format (satellite_index, pass_index, task_index).
#             - Value (tuple[int]): Indices of points that can be covered by the task. An empty tuple indicates the task covers no points.
#             The dictionary is sorted in ascending order based on the number of points each task can cover.

#     Returns:
#         tuple[int, int, int]: The key of the highest priority task combination (satellite_index, pass_index, task_index).
#     """

#     # The task prioritization logic is dynamically generated by LLM following the above principles to maximize coverage.
#     return 0

def priority(sorted_combinations: dict) -> tuple[int, int, int]:
    """
    Get the combination of task id and its coverage that that should be prioritised from the sorted combinations,
    and remove it from the list.
    The function that determine the priority should be generated by LLM

    Args:
        sorted_combinations: dict, sorted combinations of task id and its coverage. The key is a tuple, in the format of [index of satellite, index of pass, index of task], and the value is a tuple, containing the indices of points that can be covered by the task. The tuple is likely to be empty, and if so, it means that the corresponding task cannot cover any point. The dict is sorted in ascending order on the number of points that can be covered.

    Returns:
        tuple[int, int, int], the combination that is prioritised,
        in the format of [satellite index, pass index, task index], i.e. the key of the prioritised task.

    """

    return (0, 0, 0)

def update_total_coverage(selected_task: tuple, sorted_combination: dict) -> dict:
    """
    Update the total coverage based on the selected task, and remove the selected task from the sorted combinations.

    Args:
        selected_task: tuple[int, int, int], the selected task that should be removed from the sorted combinations, and the points that has been covered by it should be removed from other remaining tasks.
        sorted_combination: dict, sorted combinations of task id and its coverage. The key is a tuple, in the format of [index of satellite, index of pass, index of task], and the value is a tuple, containing the indices of points that can be covered by the task. The tuple is likely to be empty, and if so, it means that the corresponding task cannot cover any point. The dict is sorted in ascending order on the number of points that can be covered.

    Returns:
        dict, updated total coverage based on the selected task.

    """
    newly_covered_points = sorted_combination[selected_task]
    del sorted_combination[selected_task]
    for key, value in sorted_combination.items():
        sorted_combination[key] = tuple(point for point in value if point not in newly_covered_points)
    sorted_combination = dict(sorted(sorted_combination.items(), key=lambda item: len(item[1])))

    return sorted_combination


def main(dataset: dict, constraints: list) -> list:
    """
    Main function for task allocation.

    Args:
        dataset: dict, all the data needed for task allocation, including
            dataset['sat']: int, number of the satellites in the system.
            dataset['pass']: tuple, number of the passes for each satellite.
            dataset['points']: int, number of grid points in the given area.
            dataset['tasks']: dict, sorted combinations of task id and its coverage. The key is a tuple, in the format of [index of satellite, index of pass, index of task], and the value is a tuple, containing the indices of points that can be covered by the task. The tuple is likely to be empty, and if so, it means that the corresponding task cannot cover any point. The dict is sorted in ascending order on the number of points that can be covered.
        constraints: list, constraints for task allocation, containing maximum accumulated working time
        per pass, maximum working time per image, minimum working time per image, and maximum image per pass.

    Returns:
        list, selected tasks for each satellite in each pass.

    """
    max_time_per_pass = constraints[0]
    max_time_per_image = constraints[1]
    min_time_per_image = constraints[2]
    max_image_per_pass = constraints[3]

    sat_num = dataset['sat']
    pass_num = dataset['pass']
    sorted_combinations = dataset['tasks']

    # Initialization
    final_schedule = [[] for _ in range(sat_num)]  # Record assigned tasks
    mission_time_tracker = [[] for _ in range(sat_num)]  # Record the total time of assigned tasks
    for i in range(sat_num):
        final_schedule[i] = [[] for _ in range(pass_num[i])]

    # Greedy algorithm
    covered_points = set()  # Record the points that have been covered
    while sorted_combinations:
        try:
            (sat_idx, pass_idx, task_idx) = priority(sorted_combinations)
        except:
            (sat_idx, pass_idx, task_idx) = sorted(sorted_combinations.keys())[0]
        if len(sorted_combinations[(sat_idx, pass_idx, task_idx)]) <= 0:
            break
        task_points = sorted_combinations[(sat_idx, pass_idx, task_idx)]
        # if this task is able to apply
        if len(final_schedule[sat_idx][pass_idx]) < max_image_per_pass:
            new_covered_points = set(task_points) - covered_points
            # If the task can cover points that have not been covered yet
            if new_covered_points:
                final_schedule[sat_idx][pass_idx].append(task_idx)
                covered_points.update(task_points)
                # update the dict
                sorted_combinations = update_total_coverage(
                    selected_task=(sat_idx, pass_idx, task_idx), sorted_combination=sorted_combinations)
            else:
                del sorted_combinations[(sat_idx, pass_idx, task_idx)]
        else:
            del sorted_combinations[(sat_idx, pass_idx, task_idx)]

    return final_schedule

@funsearch.run
def evaluator(
        datasets: dict = dataset.datasets['24hr'],
        constraints: list = [300, 60, 10, 5],
    ) -> float:
    """
    Evaluation function for the algorthm of task allocation.

    Args:
        dataset: dict, all the data needed for task allocation, including
            dataset['sat']: int, number of the satellites in the system.
            dataset['pass']: tuple, number of the passes for each satellite.
            dataset['points']: int, number of grid points in the given area.
            dataset['tasks']: dict, sorted combinations of task id and its coverage. The key is a tuple, in the format of [index of satellite, index of pass, index of task], and the value is a tuple, containing the indices of points that can be covered by the task. The tuple is likely to be empty, and if so, it means that the corresponding task cannot cover any point. The dict is sorted in ascending order on the number of points that can be covered.
        constraints: list, constraints for task allocation, containing maximum accumulated working time
        per pass, maximum working time per image, minimum working time per image, and maximum image per pass.

    Returns:
        float, evaluation result, which is coverage level in percentage, the higher, the better.

    """

    max_time_per_pass = constraints[0]
    max_time_per_image = constraints[1]
    min_time_per_image = constraints[2]
    max_image_per_pass = constraints[3]

    optimized = []

    for name in datasets:

        if name == 'PAC':
            break

        dataset_instance = datasets[name]
        sat_num = dataset_instance['sat']
        pass_num = dataset_instance['pass']
        sorted_combinations = dataset_instance['tasks']
        num_grid_points = dataset_instance['points']
        baseline = dataset_instance['baseline']

        # Initialization
        final_schedule = [[] for _ in range(sat_num)]  # Record assigned tasks
        mission_time_tracker = [[] for _ in range(sat_num)]  # Record the total time of assigned tasks
        for i in range(sat_num):
            final_schedule[i] = [[] for _ in range(pass_num[i])]

        initial_dataset = copy.deepcopy(sorted_combinations)

        # Greedy algorithm
        covered_points = set()  # Record the points that have been covered
        while sorted_combinations:
            try:
                (sat_idx, pass_idx, task_idx) = priority(sorted_combinations)
            except:
                (sat_idx, pass_idx, task_idx) = sorted(sorted_combinations.keys())[0]
            if len(sorted_combinations[(sat_idx, pass_idx, task_idx)]) <= 0:
                break
            task_points = sorted_combinations[(sat_idx, pass_idx, task_idx)]
            # if this task is able to apply
            if len(final_schedule[sat_idx][pass_idx]) < max_image_per_pass:
                new_covered_points = set(task_points) - covered_points
                # If the task can cover points that have not been covered yet
                if new_covered_points:
                    final_schedule[sat_idx][pass_idx].append(task_idx)
                    covered_points.update(task_points)
                    # update the dict
                    sorted_combinations = update_total_coverage(
                        selected_task=(sat_idx, pass_idx, task_idx), sorted_combination=sorted_combinations)
                else:
                    del sorted_combinations[(sat_idx, pass_idx, task_idx)]
            else:
                del sorted_combinations[(sat_idx, pass_idx, task_idx)]

        # Evaluate the algorithm
        covered_points = set()  # Record the points that have been covered
        for sat_idx in range(sat_num):
            for pass_idx in range(pass_num[sat_idx]):
                if final_schedule[sat_idx][pass_idx]:
                    for task_idx in final_schedule[sat_idx][pass_idx]:
                        task_points = initial_dataset[(sat_idx, pass_idx, task_idx)]
                        covered_points.update(task_points)

        # Number of the points that have been covered
        num_covered_points = len(covered_points)
        # Coverage level in percentage

        coverage_level = num_covered_points / num_grid_points * 100

        optimized.append(coverage_level/baseline* 100)

        # 输出baseline和optimized
        print(f"baseline: {baseline}, coverage_level: {coverage_level}")
        print(f"optimized: {optimized}")

    #     optimized.append(coverage_level - baseline)

    return np.mean(optimized)
