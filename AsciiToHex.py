# import numpy as np
import binascii
import string
import re
import sys
import os
import time
import datetime
# from operator import xor
import tkinter
from tkinter import filedialog
from tkinter import *

top = tkinter.Tk()
frame = tkinter.Frame(top)
frame.grid()

if os.path.exists('editable.txt'):
    os.remove('editable.txt')
else:
    pass
if os.path.exists('new_dc9.dc9'):
    os.remove('new_dc9.dc9')
else:
    pass


# from sys import argv
# script, number_app = argv # we ask the user how many app are present in dc9

def split_records(dc9):

    full_dc9 = open(dc9, 'rb')

    record_num = 0
    record_name = dc9[:-4].rpartition('/')[-1] + f'_record_{record_num+1}.dc9'
    dc9_record = open(record_name, 'wb')
    # print(dc9[:-4].rpartition('/')[-1] + f'_record_{record_num}.dc9')

    row_num = 0
    records_list = [record_name]
    for readable_row in full_dc9.readlines():
        row_num += 1
        if b'#END##END#' in readable_row:
            # print(f'row {row_num}')
            # end_index = readable_row.find(b'#END##END#') + 10 # 10 is the length of #END##END#

            dc9_record.write(readable_row) # write the last line of the record

            # create a new file
            record_num += 1
            record_name = dc9[:-4].rpartition('/')[-1] + f'_record_{record_num+1}.dc9'
            records_list.append(record_name)
            dc9_record = open(record_name, 'wb')
            # readable_row = readable_row[:end_index] # index relative to the line read

        else:
            dc9_record.write(readable_row)

        # dc9_record.flush() # this line and the one below are used to write on file in live without waiting the program to be closed
        # os.fsync(dc9_record.fileno())
    # dc9_name = dc9[:-4] + '_record_1.dc9'
    # print(dc9_name)
    #
    # print(records_list[:-1]) # last component is always empty

    return dc9, record_num, records_list


def hex_translator(dc9_name):

    # output = open('temp.txt', 'w')

    dc9 = open(dc9_name, 'rb')

    header = []
    hex_code_list = []
    smc = 0
    header_1 = b''
    for row in dc9.readlines():
        readable_row = row

        #print(repr(readable_row), '\n')

        if b'#SMC#' in readable_row and smc == 0:
            smc = 1
            smc_index = readable_row.find(b'#SMC#')
            hexed = readable_row[smc_index+5:].hex()
            #print((hexed))
            # output.write(hexed)
            # print(smc_index)

            hex_code_list.append(hexed)

            # save header
            header_2 = readable_row[:smc_index+5]
            header = header_1 + header_2

        elif b'#SMC#' not in readable_row and smc == 1:
            hexed = readable_row.hex()
            #print((hexed))
            # output.write(hexed)

            hex_code_list.append(hexed)

        else:
            header_1 = readable_row


    return hex_code_list, header


def tag_discrimination(data, app):

    print(f'\n\n{app}:\n')
    index = 0
    index_old = index
    displayed = ''
    excessive_length = ''
    while index_old<len(data):

        first_byte = bin(int(data[index : index+2], 16))[2:]
        # print(first_byte)
        if first_byte[-5 :] == '11111':
            # print('ciao:', data[index+2 : index+4], ' ', bin(int(data[index+2 : index+4], 16))[2:])
            second_byte = bin(int(data[index+2 : index+4], 16))[2:]
            if len(second_byte)<8:
                second_byte = '0'*(8-len(second_byte)) + second_byte
            if  second_byte[0] == '1':
                index += 6
            else:
                index += 4
        else:
            index += 2

        tag = data[index_old : index]
        length_hex = (data[index : index+2])
        length = int(data[index : index+2], 16)
        byte_after_len = int(data[index+2 : index+4], 16)
        # print('byte', byte_after_len, data[index+2 : index+4])
        if (length == 129): # and byte_after_len == 'b0') or (length == 129 and byte_after_len == 'f8'):
            length_hex = (data[index+2 : index+4])
            length = byte_after_len
            excessive_length = (data[index : index+2])
            index += 4
            # print(f'lunghezza: {length} {type(length)}')
        elif (length == 130 and len(str(int(data[index+2 : index+4]))) == 1):
            length_hex = (data[index+2 : index+6])
            length = int(data[index+2 : index+6], 16)
            excessive_length = (data[index : index+2])
            index += 6
        else:
            index += 2

        value = data[index : index+length*2]

        index += length*2
        index_old = index

        displayed += tag + ' ' + excessive_length + length_hex + ' ' + value + '                       '
        print(f'{tag} {excessive_length} {length} {value}')
        excessive_length = ''

    return displayed


def parser(electrical_data):

    """ Function to print out data ordered by application """

    app_list = []

    app_name = []
    tlv_data = []

    end_part = electrical_data[-34 :]
    end_part_begin = electrical_data.find(end_part)
    # print(end_part_begin)

    j = 0
    index = 0
    next_hex_app_len = None
    while electrical_data[index : index+8] != end_part[: 8] and next_hex_app_len != '0000' and electrical_data[index : index+8] != ('00' + end_part[: 6]) and next_hex_app_len != 'ffff' and electrical_data[index : index+8] != ('ff' + end_part[: 6]) and next_hex_app_len != 'abcd': # conditions referred to the digits (padding) after any dc9 last app

        # print(electrical_data[index : end_part_begin])

        hex_app_len = electrical_data[index : index+4]
        # print(hex_app_len)
        app_len = 2 * int(hex_app_len, 16)
        app_name.append(electrical_data[index+4 : index+4 + app_len])
        index += 4 + app_len

        hex_tlv_len = electrical_data[index : index+8]
        tlv_len = 2 * int(hex_tlv_len, 16)
        tlv_data.append(electrical_data[index+8 : index+8 + tlv_len])
        index += 8 + tlv_len

        # print(index)

        current_app = app_name[j]
        current_tlv = tlv_data[j]

        # tag_discrimination(current_tlv, current_app)
        displayed = tag_discrimination(current_tlv, current_app)
        app_list.append(hex_app_len + '  ' + current_app + '      ' + hex_tlv_len + '      ' + displayed)
        # app_list.append(hex_app_len + '     ' + current_app + '     ' + hex_tlv_len + '     ' + ' '.join([current_tlv[i:i+2] for i in range(0, len(current_tlv), 2)]))
        # print(app_list[j] + '\n\n\n\n\n\n')

        next_hex_app_len = electrical_data[index : index+4]

        j += 1

    end_of_file = electrical_data[index :]

    return app_list, end_of_file, j

def length_calculator(edited, app_list):

    """ Function that check electrical data and writes the correct app length after user editing """

    new_list = []
    for line in edited.readlines():
        line = line.replace(' ', '').rstrip('\n')

        app_name_len = 2 * int(line[: 4], 16)
        # print(app_name_len)
        app_name = line[4 : 4+app_name_len]
        electric_old_len = line[4+app_name_len : 4+app_name_len+8]
        # print(electric_old_len)

        el_data = line[4+app_name_len+8 :]
        electric_new_len = len(el_data)
        electric_new_len_hex = hex(int(electric_new_len/2))[2 :]

        if len(electric_new_len_hex) < 8:
            electric_new_len_hex = '0'* (8-len(electric_new_len_hex)) + electric_new_len_hex
        # print(electric_new_len_hex)

        new_list.append(line[: 4] + app_name + electric_new_len_hex + el_data)
    # print(new_list)

    edited_stripped = ''.join(new_list).translate({ord(c): None for c in string.whitespace})
    # print(edited_stripped)

    return edited_stripped


def xor_function(electrical_data):

    """ Function that gets electrical_data and returns the checksum """

    data = electrical_data[:-34]
    # print('\n\n' + data + '\n\n\n')
    checksum = 0
    group = []

    if (len(data)/2)%4 == 0:
        pass
    else:
        remainder = len(data)%4
        data += remainder * '0'
        # print(data)

    # create a list with hex values
    data_listed = re.findall('.{1,2}', data)
    rows_num = int(len(data_listed)/4)
    # print('\n\n',data_listed,'\n\n\n')

    array = [[0 for x in range(4)] for y in range(rows_num)]
    # array = np.empty([rows_num, 4]) # would only work with numbers
    counter = 0

    for row in range(0, rows_num):
        for column in range(0, 4):
            array[row][column] = data_listed[counter]
            counter += 1

        # print(array[row])

    checksum = []
    checksum_column_1 = int(array[0][0], 16)
    checksum_column_2 = int(array[0][1], 16)
    checksum_column_3 = int(array[0][2], 16)
    checksum_column_4 = int(array[0][3], 16)

    # for column in range(0, 4):
    #     print('\n\n\n')
    for row in range(1, rows_num):
        # print((array[row][0]))
        checksum_column_1 ^= int(array[row][0], 16) # xor between hex values
        checksum_column_2 ^= int(array[row][1], 16) # xor between hex values
        checksum_column_3 ^= int(array[row][2], 16) # xor between hex values
        checksum_column_4 ^= int(array[row][3], 16) # xor between hex values
        # checksum_column = xor(checksum_column, int(array[row][column], 16)) # 'operator' module implemented xor function
        if row == rows_num-2:
            checksum_column_1_bef_last = checksum_column_1
    # print(checksum_column_1_bef_last, int(array[rows_num - 1 ][0], 16))

    # print('\n\n\n\n', hex(checksum_column_1), hex(checksum_column_2), hex(checksum_column_3), hex(checksum_column_4))
    checksum.append(hex(checksum_column_1)[2:])
    checksum.append(hex(checksum_column_2)[2:])
    checksum.append(hex(checksum_column_3)[2:])
    checksum.append(hex(checksum_column_4)[2:])

    for i in range(0, 4):
        if len(checksum[i]) < 2:
            checksum[i] = '0' + checksum[i]
        else:
            pass
    # print(checksum)

    return checksum # list containing the xor of every column

def binary_converter(header, useless_electric, new_electrical_data, checksum, end_of_file):

    """ Function to convert hex data back to binary """

    new_dc9  = open('new_dc9.dc9', 'ab')
    new_dc9.write(header)

    useless_binary = binascii.unhexlify(useless_electric)
    new_dc9.write(useless_binary)

    # print(new_electrical_data)
    back_to_binary = binascii.unhexlify(new_electrical_data)
    new_dc9.write(back_to_binary)
    # print(back_to_binary)

    checksum_bin = binascii.unhexlify(checksum)
    new_dc9.write(checksum_bin)
    # print(checksum_bin)

    fixed_bottom = binascii.unhexlify(end_of_file[-26:])
    # print(fixed_bottom)
    new_dc9.write(fixed_bottom)

dc9_name =  filedialog.askopenfilename(initialdir = "/Desktop",title = "Select file",filetypes = (("dc9 files","*.dc9"),("all files","*.*")))
dc9 = dc9_name.rpartition('/')[-1]

splitted_dc9_name, record_num, records_list = split_records(dc9_name)
print(f'\nThe selected dc9 includes {record_num} records')

for record_file_name in records_list[:-1]:
    list_hex, header = hex_translator(record_file_name)
    # print('\n\n\n\n\n\n', list_hex)
    # print('\n\n\n\n\n\n', header)

    single_string = ''.join(list_hex)
    # print(single_string)

    fixed_parameters = 28 + 24 + 4 + 2
    useless_electric = single_string[: fixed_parameters]
    electrical_data = single_string[fixed_parameters :]
    # print('ELECTRICAL DATA' + electrical_data + '\n\n\n\n\n')

    print(f'\n\n\n{record_file_name}:') # CONTAINS #{number_app} APPLICATIONS')
    app_list, end_of_file, number_app = parser(electrical_data)

    # print(app_list)
    # convert back to binary
    # binary_converter(header, single_string, end_of_file)


    editable = open('editable.txt', 'w')

    for elements in app_list:
        # print(elements)
        editable.write(elements + '\n')

    editable.flush()
    os.fsync(editable.fileno())

    next = input('\n\nYOU CAN NOW EDIT THE TXT FILE IN CURRENT FOLDER\nPRESS ENTER WHEN DONE WITH CHANGES')
    edited = open('editable.txt')

    # import string
    # edited_stripped = (''.join(edited.readlines()).translate({ord(c): None for c in string.whitespace}))
    # print('\n\n\nEDITED STRIPPED' + edited_stripped)
    # print('END OF FILE' + end_of_file[-26:])


    # ----------------------------------------------------------------------------------------------
    edited_stripped = length_calculator(edited, app_list)
    # print(edited_stripped)
    # ----------------------------------------------------------------------------------------------

    new_electrical_data = edited_stripped + end_of_file
    # print(new_electrical_data)

    checksum = ''.join(xor_function(new_electrical_data))

    edited_electric = new_electrical_data[:-34]

    print('\nCalculated Checksum:\n[', end = '')
    for k in range(0, 8, 2):
        if k < 6:
            print(f'\'{checksum[k:k+2]}\', ', end = '')
        else:
            print(f'\'{checksum[k:k+2]}\']')

    # print(end_of_file[-26:])
    # print(checksum + end_of_file[-26:])
    # convert back to binary
    binary_converter(header, useless_electric, edited_electric, checksum, end_of_file)

    os.remove(record_file_name)

print('\n\n\n\n!!! DONE !!! YOU CAN OPEN THE dc9\n\n\n\n')
# top.mainloop()

os.remove(records_list[-1])
