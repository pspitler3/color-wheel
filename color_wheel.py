from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
from fuzzywuzzy import process


def scrape_color_data(start, finish):
    """
    Scrapes the colors on wiki and puts it in a matrix.

    :param start: The start range letter (must align with wiki website)
    :param finish: The finish range letter (must align with wiki website)
    :return: Color matrix
    """

    page = requests.get('http://en.wikipedia.org/wiki/List_of_colors:_' + start + '-' + finish)
    soup = BeautifulSoup(page.text)
    color_table = soup.find('caption', text='Color names').parent

    color_array = []
    num_cols = len(color_table.findAll('tr')[0].findAll('th'))
    for rowHead in color_table.findAll('tr'):
        for rowData in rowHead.find_all(['th', 'td']):
            if len(rowData) > 1 and rowData.a:
                color_array.append(rowData.a.get_text())
            elif len(rowData) > 1:
                color_array.append(rowData.contents[1].string)
            else:
                color_array.append(rowData.get_text().strip('%'))

    color_array = np.mat(color_array)
    color_matrix = color_array.reshape(np.size(color_array) / num_cols, num_cols)

    return color_matrix


def color_df():
    """
    Runs the scrapes for the wiki colors and compiles them into an intuitive data frame.

    :return: Data frame that contains all colors and values.
    """
    af_data = scrape_color_data('A', 'F')
    gm_data = scrape_color_data('G', 'M')
    nz_ata = scrape_color_data('N', 'Z')

    color_data = np.concatenate((af_data[1:, 0:5], gm_data[1:, 0:5], nz_ata[1:, 0:5]), axis=0)
    headers = np.squeeze(np.asarray(af_data[0, 0:5]))

    color_data_frame = pd.DataFrame(data=color_data, columns=headers)
    color_data_frame['Red'] = color_data_frame['Red'].convert_objects(convert_numeric=True) / 100.0 * 255
    color_data_frame['Green'] = color_data_frame['Green'].convert_objects(convert_numeric=True) / 100.0 * 255
    color_data_frame['Blue'] = color_data_frame['Blue'].convert_objects(convert_numeric=True) / 100.0 * 255
    color_data_frame = color_data_frame.replace({'Name': {'( \(.*\))': ''}}, regex=True)
    color_data_frame = color_data_frame.drop_duplicates(['Name'])
    color_data_frame = color_data_frame.reset_index(drop=True)

    return color_data_frame


def get_clean_colors(real_colors, dirty_vector):
    """
    This takes in a vector and returns the "clean" color and RGB values.

    :param real_colors: This is a dataframe that gets created with the color_df() function.
    :param dirty_vector: This is the dirty color vector.
    :return: Clean color, match percent, hex code, and RGB values.
    """
    clean_colors = []
    choices = real_colors['Name']
    for dirty_color in dirty_vector:
        clean_colors.append(process.extractOne(dirty_color, choices))

    clean_colors = np.mat(clean_colors)
    clean_colors = clean_colors.reshape(len(dirty_vector), 2)
    clean_colors = pd.DataFrame(data=clean_colors, columns=['Color', 'match_pct'])

    clean_colors = clean_colors.reset_index().merge(real_colors, how='inner', left_on='Color', right_on='Name',
                                                    sort=False, suffixes=('', '_x')).sort('index')
    clean_colors = clean_colors.drop('Name', axis=1)
    clean_colors = clean_colors.reset_index(drop=True)
    clean_colors = clean_colors.drop('index', axis=1)

    return clean_colors


def main():
    """
    Color Wheel can be used by feeding a simple list of colors to
    get_clean_colors. So an example use case is:
    """

    vector = ['blue', 'red', 'hazel', 'black', 'green']
    clean_colors = get_clean_colors(color_df(), vector)
    print(vector)
    print(clean_colors)

if __name__ == "__main__":
    main()
