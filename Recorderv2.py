import subprocess
import time
import os
import threading

class StreamerMonitor:
    def __init__(self, streamer_name, output_folder, log_file, quality="best", check_interval=60):
        self.streamer_name = streamer_name
        self.output_folder = output_folder
        self.log_file = log_file
        self.quality = quality
        self.check_interval = check_interval
        self.is_running = True
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        
        self.log = open(self.log_file, "a")
        self.log.write(f"\n=== Started Monitoring {self.streamer_name} at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    def log_message(self, message):
        print(message.strip())
        self.log.write(message)

    def check_and_record(self):
        while self.is_running:
            try:
                result = subprocess.run(
                    ["streamlink", f"twitch.tv/{self.streamer_name}", self.quality, "--stream-url"],
                    capture_output=True,
                    text=True
                )
                self.log.write(result.stdout)
                self.log.write(result.stderr)

                if "No playable streams found" in result.stderr:
                    message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {self.streamer_name} is not live. Checking again in {self.check_interval} seconds...\n"
                    self.log_message(message)
                    time.sleep(self.check_interval)
                else:
                    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                    output_file = os.path.join(self.output_folder, f"{self.streamer_name}_{timestamp}.mp4")
                    message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Recording {self.streamer_name}'s stream to {output_file}...\n"
                    self.log_message(message)

                    process = subprocess.Popen(
                        ["streamlink", f"twitch.tv/{self.streamer_name}", self.quality, "--output", output_file],
                        stdout=self.log,
                        stderr=self.log
                    )
                    
                    process.wait()
                    end_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {self.streamer_name}'s stream ended. Monitoring for the next stream...\n"
                    self.log_message(end_message)
                    time.sleep(self.check_interval)
            except Exception as e:
                error_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - An error occurred: {str(e)}\n"
                self.log_message(error_message)
                time.sleep(self.check_interval)

    def stop(self):
        self.is_running = False
        self.log_message(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Stopped monitoring {self.streamer_name}.\n")
        self.log.close()

class StreamMonitorManager:
    def __init__(self):
        self.monitors = []

    def add_monitor(self, streamer_name, output_folder, log_file, quality="best", check_interval=60):
        monitor = StreamerMonitor(streamer_name, output_folder, log_file, quality, check_interval)
        self.monitors.append(monitor)

    def load_streamers_from_file(self, filename, output_base_folder, quality="best", check_interval=60):
        """Load streamer names from a text file and create monitors for each."""
        try:
            with open(filename, 'r') as file:
                for line in file:
                    streamer_name = line.strip()
                    if streamer_name:  # Skip empty lines
                        # Create streamer-specific output folder and log file
                        output_folder = os.path.join(output_base_folder, streamer_name)
                        log_file = os.path.join(output_base_folder, f"{streamer_name}_log.txt")
                        self.add_monitor(streamer_name, output_folder, log_file, quality, check_interval)
            print(f"Loaded {len(self.monitors)} streamers from {filename}")
        except FileNotFoundError:
            print(f"Error: {filename} not found!")
        except Exception as e:
            print(f"Error loading streamers: {str(e)}")

    def start_all(self):
        for monitor in self.monitors:
            thread = threading.Thread(target=monitor.check_and_record, daemon=True)
            thread.start()
        print("All monitors are running. Press Ctrl+C to stop.")

    def stop_all(self):
        for monitor in self.monitors:
            monitor.stop()

if __name__ == "__main__":
    manager = StreamMonitorManager()

    # Load streamers from file
    manager.load_streamers_from_file(
        filename="streamers.txt",
        output_base_folder=r".\twitch",
        quality="best",
        check_interval=60
    )

    try:
        manager.start_all()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all monitors...")
        manager.stop_all()