from garmin_fit_sdk import Decoder, Stream
from glob import glob

def generate_stats(fitfolder):
    files = glob(fitfolder+"*")
    for file in files:
        get_grades(file)

def get_grades(fitfile):
    stream = Stream.from_file(fitfile)
    decoder = Decoder(stream)
    messages, errors = decoder.read()
    splits = messages['split_mesgs']

    for split in splits:
        expected_keys = set([70, 'total_elapsed_time', 71, 15])
        

        time = split['total_elapsed_time']
        minutes = int(time // 60)
        seconds = int(time - (minutes * 60))
        prettyTime = f"{minutes}:{seconds:02d}"
        print()
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
        print()

