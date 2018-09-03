
from datetime import datetime, timedelta
import argparse
import csv


def main():
    """
    Prints the arguments being passed to the script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str)
    parser.add_argument('--date', type=str)
    args = parser.parse_args()

    day = datetime.today()
    if args.date:
        day = datetime.strptime(args.date, "%m/%d/%Y")

    # First line of output, second line is blank
    output = [day.strftime('%A') + ' ' + day.strftime("%m/%d/%Y"), '']

    # Return the day of the week as an integer, where Monday is 0 and Sunday is 6
    theater = Theater(day_of_week=day.weekday())

    with open(args.filename, "r+") as f:
        file_reader = csv.reader(f, delimiter=",")
        # Skip first line because of header
        next(file_reader)
        for line in file_reader:

            cur_movie = Movie(line)
            output.append(str(cur_movie))
            showtimes_for_movie = theater.showtimes(cur_movie)
            if len(showtimes_for_movie) == 0:
                output.append("No Showtimes For This Movie")
            for time_str in showtimes_for_movie:
                output.append(time_str)
            output.append('')

    # Do the final printing. In another world this could be written to files/db
    for print_line in output:
        print(print_line)


class Movie:
    def __init__(self, line):
        self.title = line[0]
        self.release_year = line[1]
        self.rating = line[2]
        self.hour_min_str = line[3]
        self.total_minutes = time_str_to_minutes(self.hour_min_str)

    def __str__(self):
        return self.title + " - Rated " + self.rating + ", " + self.hour_min_str


def _time_str_to_hours_minutes(hour_minute_str):
    hours = int(hour_minute_str.split(':')[0])
    minutes = int(hour_minute_str.split(':')[1])
    return hours, minutes


def time_str_to_minutes(hour_minute_str):
    hours, minutes = _time_str_to_hours_minutes(hour_minute_str)
    return hours * 60 + minutes


# By default this function rounds up the total_min (int) to the multiple (int)
def round_to_multiple(total_min, multiple, round_down=False):
    if total_min % multiple == 0:
        return total_min
    # NOTE: The double '/' does standard integer division
    rounded_up = ((total_min // multiple) + 1) * multiple
    if not round_down:
        return rounded_up
    # Subtract one multiple if we want to round down
    return rounded_up - multiple


def minutes_to_time_hour_repr(minutes):
    hours, minutes = divmod(minutes, 60)
    hours_str = str(int(hours))
    minutes_str = str(int(minutes))
    if len(minutes_str) == 1:
        minutes_str = "0" + minutes_str
    return "{}:{}".format(hours_str, minutes_str)


EIGHT_AM = "8:00"
TEN_THIRTY_AM = "10:30"
ELEVEN_PM = "23:00"
ELEVEN_THIRTY_PM = "23:30"


class Theater:
    def __init__(self, day_of_week, time_to_open=60, time_to_change=35, start_time_multiple=5):
        self.day_of_week = day_of_week
        self.time_to_open = time_to_open
        self.time_to_change = time_to_change
        self.start_time_multiple = start_time_multiple

        # These will be specified manually if they need to change
        # For now:
        # Monday - Thursday 8:00am - 11:00pm
        # Friday - Sunday 10:30am - 11:30pm
        self.opening_times = {0: EIGHT_AM, 1: EIGHT_AM, 2: EIGHT_AM, 3: EIGHT_AM, 4:
                              EIGHT_AM, 5: TEN_THIRTY_AM, 6: TEN_THIRTY_AM}
        self.closing_times = {0: ELEVEN_PM, 1: ELEVEN_PM, 2: ELEVEN_PM, 3: ELEVEN_PM, 4:
                              ELEVEN_PM, 5: ELEVEN_THIRTY_PM, 6: ELEVEN_THIRTY_PM}
        self.today_open = self.opening_times.get(self.day_of_week)
        self.today_close = self.closing_times.get(self.day_of_week)

    # Theoretically we could open at something like 956, and it takes 3 minutes to open
    # If I round both first, the first movie can't start until 10:05
    # But it really should be able to start at 10:00. Therefore first add, then round up
    def earliest_movie_start(self):
        start_plus_open = time_str_to_minutes(self.today_open) + self.time_to_open
        return round_to_multiple(start_plus_open, self.start_time_multiple)

    def showtimes(self, movie):
        # For a given movie, return a list of showings (start-time, endtime)
        start_showtimes = []
        end_showtimes = []
        max_ending_time = timedelta(minutes=time_str_to_minutes(self.today_close))

        while True:
            # Need to start at the consistent multiple, so we round actual start down to that multiple
            est_start_time = max_ending_time - timedelta(minutes=movie.total_minutes)
            rounded_start_time = round_to_multiple(est_start_time.seconds / 60, self.start_time_multiple,
                                                   round_down=True)
            actual_start_time = timedelta(minutes=rounded_start_time)

            # Base base: Can't start any movies before the earliest movie start time
            if actual_start_time < timedelta(minutes=self.earliest_movie_start()):
                break

            # Movie actually ends at actual_start + total+minutes (no rounding)
            end_time = actual_start_time + timedelta(minutes=movie.total_minutes)

            start_showtimes.append(minutes_to_time_hour_repr(actual_start_time.seconds/60))
            end_showtimes.append(minutes_to_time_hour_repr(end_time.seconds/60))

            # Set the next max ending time to before when the other move starts
            max_ending_time = actual_start_time - timedelta(minutes=self.time_to_change)

        # As a safety check the final movie should end within start_time_multiple of closing
        # Used for testing/debugging, commented out for now

        # if time_str_to_minutes(self.today_close) - \
        #         time_str_to_minutes(end_showtimes[0]) > self.start_time_multiple:
        #     print("This should not happen")

        # I need the showtimes reversed and in a string format for printing
        output_format = []
        for start_end in zip(reversed(start_showtimes), reversed(end_showtimes)):
            output_format.append('  {} - {}'.format(start_end[0], start_end[1]))
        return output_format


def run_tests():
    test_round_to_multiple()
    test_minutes_to_time_hour_repr()
    test_movie_to_str()
    test_subtract_hour_min_strs()


def test_round_to_multiple():
    assert round_to_multiple(44, 5) == 45
    assert round_to_multiple(0, 5) == 0
    assert round_to_multiple(15, 5) == 15
    assert round_to_multiple(31, 5) == 35

    assert round_to_multiple(31, 5, round_down=True) == 30
    assert round_to_multiple(44, 5, round_down=True) == 40
    assert round_to_multiple(15, 15, round_down=True) == 15
    assert round_to_multiple(0, 5, round_down=True) == 0
    assert round_to_multiple(29, 30, round_down=True) == 0


def test_minutes_to_time_hour_repr():
    assert minutes_to_time_hour_repr(0) == "0:00"
    assert minutes_to_time_hour_repr(43) == "0:43"
    assert minutes_to_time_hour_repr(61) == "1:01"
    assert minutes_to_time_hour_repr(75) == "1:15"
    assert minutes_to_time_hour_repr(120) == "2:00"


def test_movie_to_str():
    correct_str = "There's Something About Mary - Rated R, 2:14"
    movie = Movie(["There's Something About Mary", "1998", "R", "2:14"])
    assert str(movie) == correct_str


# I did not end up using this but figured I'd leave it here anyway
def subtract_hour_min_strs(hour_min_str_a, hour_min_str_b):
    # This returns an hour_min_str of 24 hour format
    # hour_min_str_a should be bigger
    a_min = time_str_to_minutes(hour_min_str_a)
    b_min = time_str_to_minutes(hour_min_str_b)
    minutes = timedelta(minutes=a_min) - timedelta(minutes=b_min)
    return minutes_to_time_hour_repr(minutes.seconds/60)


def test_subtract_hour_min_strs():
    assert subtract_hour_min_strs("1:00", "0:40") == "0:20"
    assert subtract_hour_min_strs("3:30", "0:40") == "2:50"
    assert subtract_hour_min_strs("23:59", "1:02") == "22:57"


if __name__ == '__main__':
    # run_tests()
    main()
