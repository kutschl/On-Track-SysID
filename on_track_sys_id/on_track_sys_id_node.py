import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped
from ament_index_python.packages import get_package_share_directory

import numpy as np 
import os 
import yaml
import csv
from datetime import datetime
from tqdm import tqdm

from on_track_sys_id.helpers.train_model import nn_train


class OnTrackSysID(Node):
    
    def __init__(self):
        super().__init__(
            node_name='on_track_sys_id',
            allow_undeclared_parameters=True,
            automatically_declare_parameters_from_overrides=True
        )
        
        self.get_logger().info("Initializing...")
        
        # ROS parameters
        self.update_rate = self.get_parameter('update_rate').get_parameter_value().integer_value
        self.racecar_version = self.get_parameter('racecar_version').get_parameter_value().string_value
        self.odom_topic = self.get_parameter('odom_topic').get_parameter_value().string_value
        self.ackermann_drive_topic = self.get_parameter('ackermann_drive_topic').get_parameter_value().string_value
        self.save_LUT_name = self.get_parameter('save_LUT_name').get_parameter_value().string_value
        self.plot_model = self.get_parameter('plot_model').get_parameter_value().bool_value
        
        self.package_path = get_package_share_directory('on_track_sys_id')
        
        self.load_nn_params()
        
        # Data storage
        self.data_duration = self.nn_params['data_collection_duration']
        self.timesteps = self.data_duration * self.update_rate
        self.data: np.ndarray = np.zeros((self.timesteps, 4))
        self.counter: int = 0
        self.current_state: np.ndarray = np.zeros(4)
        '''NDarray with current state (vx, vy, yaw rate, steering angle)'''
        
        # Loop functionality
        self.loop_rate = self.create_rate(self.update_rate)
        self.loop_progress_bar = tqdm(total=self.timesteps, desc='Collecting data', ascii=True)
        
        # Subscriptions
        self.odom_sub = self.create_subscription(Odometry, self.odom_topic, self.odom_cb, 10)
        self.drive_sub = self.create_subscription(AckermannDriveStamped, self.ackermann_drive_topic, self.ackermann_drive_cb, 10)
        
        self.get_logger().info("Successfully initialized!")
    
    
    def load_nn_params(self):
        """
        This function loads parameters neural network parameters from 'params/nn_params.yaml' and stores them in self.nn_params.
        """
        yaml_file = os.path.join(self.package_path, 'params/nn_params.yaml')
        with open(yaml_file, 'r') as file:
            self.nn_params = yaml.safe_load(file)
                
        
    def export_data_as_csv(self):
        """
        Export collected data as a CSV file.

        Prompts the user to confirm exporting data. If confirmed, data is saved as a CSV file
        including velocity components (v_x, v_y), yaw rate (omega), and steering angle (delta).
        """
        # Prompt user for confirmation to export data
        user_input = input("\033[33m[WARN] Press 'Y' and then ENTER to export data as CSV, or press ENTER to continue without dumping: \033[0m")
        if user_input.lower() == 'y':
            data_dir = os.path.join(self.package_path, 'data', self.racecar_version)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = os.path.join(data_dir, f'{self.racecar_version}_sys_id_data_{timestamp}.csv')
            
            # Write data to CSV file    
            with open(csv_file, mode='w') as file:
                writer = csv.writer(file)
                writer.writerow(['v_x', 'v_y', 'omega', 'delta'])
                for row in self.data:
                    writer.writerow(row)  # Each row contains v_x, v_y, omega, delta
            self.get_logger().info(f"Data has been exported to: {csv_file}")


    def odom_cb(self, data: Odometry):
        self.current_state[0] = data.twist.twist.linear.x
        self.current_state[1] = data.twist.twist.linear.y
        self.current_state[2] = data.twist.twist.angular.z
        
    
    def ackermann_drive_cb(self, data: AckermannDriveStamped):
        self.current_state[3] = data.drive.steering_angle
    
    def collect_data(self):
        """
        Collects data during simulation.

        Adds the current state to the data array and updates the counter.
        Closes the progress bar and logs a message if data collection is complete.
        """
        
        if self.current_state[0] > 1: # Only collect data when the car is moving
            self.data = np.roll(self.data, -1, axis=0)
            self.data[-1] = self.current_state
            self.counter += 1
            self.loop_progress_bar.update(1)
        if self.counter == self.timesteps + 1:
            self.loop_progress_bar.close()
            self.get_logger().info("Data collection completed.")
            
    def run_nn_train(self):
        """
        Initiates training of the neural network using collected data.
        """
        self.get_logger().info("Training neural network...")
        nn_train(self.data, self.racecar_version, self.save_LUT_name, self.plot_model)
        
        
    def loop(self):
        while rclpy.ok():
            self.collect_data()

            if self.counter >= self.timesteps:
                self.run_nn_train()
                self.export_data_as_csv()
                self.get_logger().info("Training completed. Shutting down...")

                rclpy.shutdown()
                break  # break while-loop after shutdown

            self.loop_rate.sleep()


def main():
    rclpy.init()
    on_track_sys_id = OnTrackSysID()
    on_track_sys_id.loop()


if __name__ == '__main__':
    main()