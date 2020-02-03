#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 03 22:37:00 2020
@author: Dennis Gross
"""
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

def build_dict_from_csv_file(path, primary_column, ignore_columns = ["pull up bar", "comments"]):
    """
        Load exercises dynamically.
        Args:
            path to CSV-file.
            primary_column is the name of the exercise.
            ignore_columns, which columns should be ignored in the CSV-file.
        Returns:
            dictionary {('Diamond push ups', 'abs'): 0.25,('Diamond push ups', 'shoulders'): 0.0, 
                ('Diamond push ups', 'triceps'): 0.75,
                ('bridge', 'abs'): 0.5,...}
    """
    df = pd.read_csv(path)
    df = df.drop(ignore_columns, axis=1)
    df = df.fillna(0)
    return df.set_index([primary_column]).stack().to_dict()

def exercise_and_time_dict(multi_dict, time = 1):
    """
        Creates a dictionary exercise : time. This is used to create the gurobi multi dictionary more easily.
        Args:
            The dictionary with the exercises and intensities.
            time, 1 minute by default.
        Returns:
            The needed time for each exercise. It is always 1 because we want that our exercises take 1 minute each.
            {'Diamond push ups': 1,
                'bridge': 1,
                'bulgarian split squats': 1,...}
    """
    d = {}
    for key in list(multi_dict):
        d[key[0]] = time
    return d

if __name__ == "__main__":
    # Define your intensities manually
    categories, min_intensity, max_intensity = gp.multidict({
        'shoulders' : [0,GRB.INFINITY],
        'back' : [0,GRB.INFINITY],
        'breast' : [0,GRB.INFINITY],
        'biceps' : [0,GRB.INFINITY],
        'triceps' : [0,GRB.INFINITY],
        'abs' : [0,GRB.INFINITY],
        'butt' : [0.5,0.5],
        'legs' : [2,2]
    })

    # Read exercises and their intensity
    exercises_intensities = build_dict_from_csv_file("exercises.csv", "name")
    # Read exercises and their needed time
    exercises, time = gp.multidict(exercise_and_time_dict(exercises_intensities))
    # Build model
    m = gp.Model("circle_training")
    # Create trainings variables (each exercise is a decision variable)
    training = m.addVars(exercises, vtype=GRB.BINARY, name="training")
    # Objective Function
    m.setObjective(training.prod(time), GRB.MINIMIZE)
    # Constraint:
    # shoulders * push ups + shoulders * biceps + ...
    # others * push ups + ....
    m.addConstrs((gp.quicksum(exercises_intensities[e, c] * training[e] for e in exercises)
        == [min_intensity[c], max_intensity[c]]
        for c in categories), "_"
    )
    # Find Solution
    m.optimize()
    # if there is a solution
    if m.status == GRB.OPTIMAL:
        print("Your training plan:")
        print('\nTime: %g' % m.objVal)
        print('\nTrain:')
        trainingx = m.getAttr('x', training)
        for f in exercises:
            if trainingx[f] > 0:
                print('%s %g' % (f, trainingx[f]))
    else:
        print('No solution')

