from garmin_fit_sdk import Decoder, Stream
from glob import glob

def generate_stats(fit_files):
    files = glob(fit_files + "/*")
    for file in files:
        stream = Stream.from_file(file)
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        get_time(messages)
        get_user_weight(messages)
        get_grades(messages)

def get_time(messages):
    file_time = messages["file_id_mesgs"][0]["time_created"]
    print(file_time)

def get_user_weight(messages):
    user_profile = messages["user_profile_mesgs"][0]
    print(user_profile.keys())
    # for key, item in user_profile.items():
    #     print(f"{key}: {item}")
    weight = user_profile["weight"]
    metric = user_profile["weight_setting"] == "statute"
    print(f"Weight: {weight}{'kg' if metric else 'lbs'}")


# get the name of person, get the weight of person, get the day it happened
def get_grades(messages):
    splits = messages['split_mesgs']
    print()
    for split in splits:
        expected_keys = set([70, 'total_elapsed_time', 71, 15])
        

        time = split['total_elapsed_time']
        minutes = int(time // 60)
        seconds = int(time - (minutes * 60))
        prettyTime = f"{minutes}:{seconds:02d}"

        if (split["split_type"] == "climb_active"):
            if (len(expected_keys.intersection(set(split.keys()))) != len(expected_keys)):
                print("CORRUPTED ROW")
                print(split.keys())
                continue
            grade = split[70]-1 if 70 in split.keys() else None
            status = ('Completed' if split[71]== 3 else 'Attempted') if 71 in split.keys() else None
            avg_hearrate = split[15] if 15 in split.keys() else None

            print(f"Grade: {grade}\t Status: {status}\t Time: {prettyTime}\t HR_AVG: {avg_hearrate}bpm")
        else:
            # print(f"Rested for: {prettyTime}")
            pass

if __name__ == "__main__":
    generate_stats("data/fit")