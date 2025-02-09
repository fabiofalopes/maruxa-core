import pyaudio
import wave
import os
import threading
from config.config import AUDIO_CONFIG, RECORDINGS_DIR
from config.setup import save_config

class AudioRecorder:
    def __init__(self, output_directory=RECORDINGS_DIR):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100  # Default, will be overridden if possible
        self.output_directory = output_directory
        self.input_device_index = AUDIO_CONFIG.get('input_device_index')

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

    def list_input_devices(self):
        try:
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')

            devices_found = False
            devices = []  # Store device info for later use
            for i in range(0, numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    device_name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                    print(f"Input Device id {i} - {device_name}")
                    devices.append({'index': i, 'name': device_name})
                    devices_found = True

            if not devices_found:
                print("No input devices found! Please check your audio settings and permissions.")
                print("You may need to:")
                print("1. Install ALSA utils: sudo apt-get install alsa-utils")
                print("2. Configure ALSA: sudo alsactl init")
                print("3. Check if your user is in the 'audio' group: sudo usermod -a -G audio $USER")
            p.terminate() # Terminate here
            return devices # Return the list of devices

        except Exception as e:
            print(f"Error listing audio devices: {e}")
            print("Try running: sudo apt-get install python3-pyaudio portaudio19-dev")
            if 'p' in locals(): # Check if p exists before terminating
                p.terminate()
            return [] # Return empty list on error


    def _get_supported_sample_rate(self, p, device_index):
        """Find the highest supported sample rate for the given device."""
        supported_rates = [48000, 44100, 32000, 24000, 16000, 8000]
        for rate in supported_rates:
            try:
                if p.is_format_supported(rate, input_device=device_index, input_channels=self.channels, input_format=self.format):
                    return rate
            except ValueError as e:
                print(f"Sample rate {rate} not supported: {e}")
                continue  # Try the next lower rate
        raise Exception("No supported sample rate found for this device.")

    def _prompt_for_device(self, p):
        """Prompts the user to select an input device."""
        devices = self.list_input_devices()
        if not devices:
            raise Exception("No input devices found.")

        while True:
            try:
                choice = int(input("Enter the number of the device you want to use: "))
                if 0 <= choice < len(devices):
                    return devices[choice]['index']
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def record_until_q(self, filename, input_device_index=None):
        try:
            os.makedirs(self.output_directory, exist_ok=True)
            p = pyaudio.PyAudio()

            # Use provided index or prompt the user
            if input_device_index is None:
                if self.input_device_index is not None:
                    # TRY to use the configured device
                    try:
                        input_device_index = self.input_device_index
                        self.rate = self._get_supported_sample_rate(p, input_device_index)
                        print(f"Using previously configured device: {input_device_index}")
                    except:
                        print("Previously configured device not available. Prompting.")
                        input_device_index = self._prompt_for_device(p)
                        save_config({'input_device_index': input_device_index})
                        self.input_device_index = input_device_index
                else:
                    # No configured device, prompt
                    input_device_index = self._prompt_for_device(p)
                    save_config({'input_device_index': input_device_index})  # Save selection
                    self.input_device_index = input_device_index

            print(f"Attempting to open stream with device {input_device_index}")
            self.rate = self._get_supported_sample_rate(p, input_device_index)
            print(f"Using sample rate: {self.rate}")

            stream = p.open(format=self.format,
                            channels=self.channels,
                            rate=self.rate,
                            input=True,
                            input_device_index=input_device_index,
                            frames_per_buffer=self.chunk)

            print("* recording")
            print("Press Ctrl+C to stop recording")
            frames = []

            while True:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                except KeyboardInterrupt:
                    break  # Exit recording loop cleanly on Ctrl+C
                except Exception as e:
                    print(f"Error during recording: {e}")
                    raise  # Re-raise other exceptions

            print("* done recording")

            stream.stop_stream()
            stream.close()
            p.terminate()

            full_path = os.path.join(os.path.abspath(self.output_directory), filename)
            print(f"Saving to directory: {os.path.dirname(full_path)}")
            print(f"Full file path: {full_path}")

            wf = wave.open(full_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            print(f"Successfully saved recording to {full_path}")
            return full_path

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

    def record(self, duration, filename, input_device_index=None):
        try:
            p = pyaudio.PyAudio()

            # Use provided index or prompt the user
            if input_device_index is None:
                if self.input_device_index is not None:
                    # TRY to use the configured device
                    try:
                        input_device_index = self.input_device_index
                        self.rate = self._get_supported_sample_rate(p, input_device_index)
                        print(f"Using previously configured device: {input_device_index}")
                    except:
                        print("Previously configured device not available. Prompting.")
                        input_device_index = self._prompt_for_device(p)
                        save_config({'input_device_index': input_device_index})
                        self.input_device_index = input_device_index
                else:
                    # No configured device, prompt
                    input_device_index = self._prompt_for_device(p)
                    save_config({'input_device_index': input_device_index})  # Save selection
                    self.input_device_index = input_device_index

            self.rate = self._get_supported_sample_rate(p, input_device_index)
            print(f"Using sample rate: {self.rate}")

            stream = p.open(format=self.format,
                            channels=self.channels,
                            rate=self.rate,
                            input=True,
                            input_device_index=input_device_index,
                            frames_per_buffer=self.chunk)

            print(f"* Recording from device {input_device_index} for {duration} seconds.")

            frames = []

            for i in range(0, int(self.rate / self.chunk * duration)):
                data = stream.read(self.chunk)
                frames.append(data)

            print("* Done recording")

            stream.stop_stream()
            stream.close()
            p.terminate()

            file_path = os.path.join(self.output_directory, filename)
            wf = wave.open(file_path, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()

            return file_path
        except Exception as e:
            print(f"An error occurred in record method: {e}")
            raise

    def record_and_transcribe(self, duration, filename, transcription_api):
        file_path = self.record(duration, filename)
        return transcription_api.transcribe_audio(file_path)
