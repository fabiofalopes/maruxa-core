import pyaudio
import wave
import os
import threading
from config.config import AUDIO_CONFIG, RECORDINGS_DIR

class AudioRecorder:
    def __init__(self, output_directory=RECORDINGS_DIR):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
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
            for i in range(0, numdevices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    print(f"Input Device id {i} - {p.get_device_info_by_host_api_device_index(0, i).get('name')}")
                    devices_found = True
            
            if not devices_found:
                print("No input devices found! Please check your audio settings and permissions.")
                print("You may need to:")
                print("1. Install ALSA utils: sudo apt-get install alsa-utils")
                print("2. Configure ALSA: sudo alsactl init")
                print("3. Check if your user is in the 'audio' group: sudo usermod -a -G audio $USER")
            
        except Exception as e:
            print(f"Error listing audio devices: {e}")
            print("Try running: sudo apt-get install python3-pyaudio portaudio19-dev")
        finally:
            p.terminate()

    def record_until_q(self, filename, input_device_index=None):
        try:
            # Ensure output directory exists
            os.makedirs(self.output_directory, exist_ok=True)
            
            p = pyaudio.PyAudio()
            
            # If no specific device is specified, try to find any working input device
            if input_device_index is None:
                for i in range(p.get_device_count()):
                    device_info = p.get_device_info_by_index(i)
                    if device_info.get('maxInputChannels') > 0:
                        input_device_index = i
                        break
                if input_device_index is None:
                    raise Exception("No working input device found")

            print(f"Attempting to open stream with device {input_device_index}")
            
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
                    break
                except Exception as e:
                    print(f"Warning: {e}")
                    continue

            print("* done recording")
            
            # Ensure proper cleanup
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
            try:
                p.terminate()
            except:
                pass

            # Save the recording
            try:
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
                print(f"Error saving the recording: {str(e)}")
                raise

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

    def record(self, duration, filename, input_device_index=None):
        p = pyaudio.PyAudio()

        if input_device_index is None:
            input_device_index = p.get_default_input_device_info()['index']

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

    def record_and_transcribe(self, duration, filename, transcription_api):
        file_path = self.record(duration, filename)
        return transcription_api.transcribe_audio(file_path)
