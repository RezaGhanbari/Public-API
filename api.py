from __future__ import print_function
import requests

CPI_DATA_URL = 'http://research.stlouisfed.org/fred2/data/CPIAUCSL.txt'


class CPIData(object):
    """
    This stores internally only one value per year
    """

    def __init__(self):
        # Each year available to the dataset will end up as a simple key-value
        # pair within this dict. We don't really need any order here so going
        # with a plain old dictionary is the best approach.
        self.year_cpi = {}

        # Later on we will also remember the first and the last year
        # we have found in the dataset  to handle years prior or after
        # the documented time span.
        self.last_year = None
        self.first_year = None

    def load_from_url(self, url, save_as_file=None):
        """Loads data from a given url.

        The downloaded file can also be saved into a location for later
        re-use with the "save_as_file" parameter specifying a filename.

        After fetching the file this implementation uses load_from_file
        internally.

        """

        # We don't really know how much data we are going to get here, so
        # it is recommended to just keep as little data as possible in memory
        # at all times. Since python-requests supports gzip-compression by
        # default and decoding these chunks on their own isn't that easy,
        # we just disable gzip with the empty "Accept-Encoding" header.
        fp = requests.get(url,
                          stream=True,
                          headers={'Accept-Encoding': None}).raw

        # If we did not pass in a save_as_file parameter, we just return the
        # raw data we got from previous line.
        if save_as_file is None:
            return self.load_from_file(fp)

        # Else, we write to the desired file.
        else:
            with open(save_as_file, 'wb+') as out:
                while True:
                    buffer = fp.read(81920)
                    if not buffer:
                        break
                    out.write(buffer)
            with open(save_as_file) as fp:
                return self.load_from_file(fp)

    def load_from_file(self, fp):
        """
        Loads CPI data from a given file-like object.
        """
        current_year = None
        year_cpi = []
        for line in fp:

            # The actual content of the file starts with a header line
            # starting with the string "DATE ". Until we reach this line
            # we can skip ahead.
            while not line.startswith("DATE "):
                pass

            # Each line ends with a new-line character which we strip here
            # to make the data easier usable.
            data = line.rstrip().split()

            # While we are dealing with calendar data the format is simple
            # enough that we don't really need a full date-parser. All we
            # want is the year which can be extracted by simple string
            # splitting:
            year = int(data[0].split("-")[0])
            cpi = float(data[1])

            if self.first_year is None:
                self.first_year = year
            self.last_year = year

            # The moment we reach a new year, we have to reset the CPI data
            # and calculate the average CPI of the current_year
            if current_year != year:
                if current_year is not None:
                    self.year_cpi[current_year] = sum(year_cpi) / len(year_cpi)
                year_cpi = []
                current_year = year
            year_cpi.append(cpi)

        # We have to do the calculation once again for the last year in the
        # data set
        if current_year is not None and current_year not in self.year_cpi:
            self.year_cpi[current_year] = sum(year_cpi) / len(year_cpi)

    def get_adjusted_price(self, price, year, current_year=None):
        """
        :return: The adapted price from a given year compared to what current
        year has been specified

        """
        if __name__ == '__main__':
            if current_year is None or current_year > 2013:
                current_year = 2013

            # if our data range doesn't provide a CPI for the given year,
            # use the edge data.
            if year < self.first_year:
                year = self.first_year
            elif year > self.last_year:
                year = self.last_year

            year_cpi = self.year_cpi[year]
            current_cpi = self.year_cpi[current_year]

            return float(price) / year_cpi * current_cpi
