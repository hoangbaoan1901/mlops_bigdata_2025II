#!/usr/bin/env python
import sys
import os
import argparse
import time

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.mlflow_config import configure_mlflow
from utils.mlflow_utils import force_terminate_run

def get_all_running_runs(mlflow):
    """Get all runs in RUNNING state"""
    try:
        # Find all experiments
        experiments = mlflow.search_experiments()
        running_runs = []
        
        for exp in experiments:
            runs = mlflow.search_runs(
                experiment_ids=[exp.experiment_id],
                filter_string="attributes.status = 'RUNNING'"
            )
            
            if not runs.empty:
                for _, run in runs.iterrows():
                    running_runs.append({
                        "run_id": run.run_id,
                        "experiment_id": exp.experiment_id,
                        "experiment_name": exp.name,
                        "start_time": run.start_time
                    })
        
        return running_runs
    except Exception as e:
        print(f"Error getting running runs: {str(e)}")
        return []

def kill_active_run(mlflow, run_id):
    """Terminate an active MLflow run using client API"""
    try:
        # Check if run exists
        run = mlflow.get_run(run_id)
        print(f"Found run {run_id} with status: {run.info.status}")
        
        # End run if it's active
        if run.info.status == "RUNNING":
            print(f"Attempting to terminate active run: {run_id}")
            try:
                mlflow.end_run(run_id=run_id)
                print(f"Run {run_id} has been terminated successfully")
                return True
            except Exception as e:
                print(f"Standard termination failed: {str(e)}")
                print("Trying force kill via REST API...")
                return force_terminate_run(run_id)
        else:
            print(f"Run {run_id} is not active (status: {run.info.status})")
            return True
    except Exception as e:
        print(f"Error checking run {run_id}: {str(e)}")
        print("Trying force kill via REST API as a last resort...")
        return force_terminate_run(run_id)

def main():
    parser = argparse.ArgumentParser(description='MLflow Run Cleanup Utility')
    parser.add_argument('--run-id', type=str, help='Specific run ID to terminate')
    parser.add_argument('--all', action='store_true', help='Terminate all active runs')
    parser.add_argument('--experiment', type=str, help='Terminate all active runs in specified experiment')
    args = parser.parse_args()
    
    # Configure MLflow
    mlflow = configure_mlflow()
    print(f"Connected to MLflow tracking server")
    
    # Specific run ID provided
    if args.run_id:
        print(f"Attempting to terminate run: {args.run_id}")
        kill_active_run(mlflow, args.run_id)
    
    # Find all active runs
    if args.all or args.experiment:
        running_runs = get_all_running_runs(mlflow)
        
        if running_runs:
            print(f"Found {len(running_runs)} active runs:")
            for run in running_runs:
                if args.experiment and run["experiment_name"] != args.experiment:
                    continue
                    
                print(f"  Run ID: {run['run_id']} (Experiment: {run['experiment_name']})")
                kill_active_run(mlflow, run['run_id'])
        else:
            print("No active runs found")
    
    # If no arguments provided, show usage
    if not (args.run_id or args.all or args.experiment):
        parser.print_help()
    
    # End any current run to be safe
    try:
        mlflow.end_run()
        print("Any active client run has been terminated")
    except Exception as e:
        print(f"Note when ending active run: {str(e)}")

if __name__ == "__main__":
    main()