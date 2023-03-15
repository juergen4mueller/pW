
import json

def save_config():
    data = {
        "GPS_serial_port":"COM4",
        "cam_type":"cv",
        "logging_active":True
    }
    with open("config.json", "wt") as cfg:
        json.dump(data, cfg)
    print("Config written")    
    
    def load_config():
         with open("config.json", "wt") as cfg:
            conf = json.load(cfg)
        
        
    if __name__ == "__main__":
        print("Config generator")
        save_config()