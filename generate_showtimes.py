# Assuming everything is timezone unaware
# Assuming movie times with runtimes < 1 hour will be formatted 0:43
# Assuming moves with times > 24 hours are still in hours:minutes


# Based on the example given, it's possible to end a movie within time_to_close
# of the movie theater closing
# aka: Something about Mary ends at 22:59 even though the theater closes at 23:00
# and it should take 35 minutes to cleanup which puts it past closing
# I hope the employees get paid those 34 minutes over overtime :)


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
            for time_str in theater.showtimes(cur_movie):
                output.append(time_str)
            output.append('')

    for print_line in output:
        print(print_line)


class Movie:
    def __init__(self, line):
        self.title = line[0]
        self.release_year = line[1]
        self.rating = line[2]
        self.hour_min_str = line[3]
        self.hours, self.minutes = _time_str_to_hours_minutes(self.hour_min_str)
        self.total_minutes = total_minutes(self.hours, self.minutes)
        # This should be a theater parameter
        self.rounded_total_minutes = round_up_to_multiple(self.total_minutes, 5)

    def __str__(self):
        return self.title + " - Rated " + self.rating + ", " + self.hour_min_str


def _time_str_to_hours_minutes(hour_minute_str):
    hours = int(hour_minute_str.split(':')[0])
    minutes = int(hour_minute_str.split(':')[1])
    return hours, minutes


def time_str_to_minutes(hour_minute_str):
    hours, minutes = _time_str_to_hours_minutes(hour_minute_str)
    return total_minutes(hours, minutes)


def total_minutes(hours, minutes):
    return hours * 60 + minutes


# Maybe some theaters will want to round up to a different multiple
def round_up_to_multiple(total_min, multiple):
    if total_min % multiple == 0:
        return total_min
    # NOTE: The double '/' does standard integer division
    return ((total_min // multiple) + 1) * multiple


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
    # Monday - Thursday 8:00am - 11:00pm
    # Friday - Sunday 10:30am - 11:30pm
    def __init__(self, day_of_week, time_to_open=60, time_to_change=35, start_time_multiple = 5):
        # These will be specified manually if they need to change
        self.opening_times = {0: EIGHT_AM, 1: EIGHT_AM, 2: EIGHT_AM, 3: EIGHT_AM, 4:
                              EIGHT_AM, 5: TEN_THIRTY_AM, 6: TEN_THIRTY_AM}
        self.closing_times = {0: ELEVEN_PM, 1: ELEVEN_PM, 2: ELEVEN_PM, 3: ELEVEN_PM, 4:
                              ELEVEN_PM, 5: ELEVEN_THIRTY_PM, 6: ELEVEN_THIRTY_PM}

        self.time_to_open = time_to_open
        self.time_to_change = time_to_change

        # It's  more important to get the rounded time
        # self.rounded_time_to_open = round_up_to_multiple(time_to_open, 5)
        self.rounded_time_to_change = round_up_to_multiple(time_to_change, 5)

        self.day_of_week = day_of_week
        self.daily_closing = self.closing_times.get(self.day_of_week)

    # Theoretically we could open at something like 956, and it takes 3 minutes to open
    # If I round both first, the first movie can't start until 10:05
    # But it really should be able to start at 10:00. Therefore add, then round
    def first_movie_start(self):
        start_plus_open = time_str_to_minutes(self.opening_times.get(self.day_of_week)) + self.time_to_open
        return round_up_to_multiple(start_plus_open, 5)

    def showtimes(self, movie):
        # For a given movie, return a list of showings (start-time, endtime)
        start_showtimes = []
        end_showtimes = []
        max_ending_time = timedelta(minutes=time_str_to_minutes(self.daily_closing))

        while True:
            # Need to start at the consistent multiple
            start_time = max_ending_time - timedelta(minutes=movie.rounded_total_minutes)

            if start_time < timedelta(minutes=self.first_movie_start()):
                break
            # Movie actually ends at total_minutes + start (no rounding)
            end_time = start_time + timedelta(minutes=movie.total_minutes)

            start_showtimes.append(minutes_to_time_hour_repr(start_time.seconds/60))
            end_showtimes.append(minutes_to_time_hour_repr(end_time.seconds/60))
            # Set the next max ending time to before when the other move starts
            max_ending_time = start_time - timedelta(minutes=self.rounded_time_to_change)

        # I need them reversed and in a string format for printing
        output_format = []
        for start_end in zip(reversed(start_showtimes), reversed(end_showtimes)):
            output_format.append('  {} - {}'.format(start_end[0], start_end[1]))
        return output_format


def run_tests():
    test_round_up_to_multiple()
    test_minutes_to_time_hour_repr()
    test_movie_to_str()
    test_subtract_hour_min_strs()


def test_round_up_to_multiple():
    assert round_up_to_multiple(44, 5) == 45
    assert round_up_to_multiple(0, 5) == 0
    assert round_up_to_multiple(15, 5) == 15
    assert round_up_to_multiple(31, 5) == 35
    # I initially misread and thought start time was multiple of 15
    assert round_up_to_multiple(31, 15) == 45
    assert round_up_to_multiple(44, 15) == 45
    assert round_up_to_multiple(0, 15) == 0
    assert round_up_to_multiple(15, 15) == 15
    assert round_up_to_multiple(31, 30) == 60


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
