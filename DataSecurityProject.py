import os
import xlwt
import shutil
import cv2
import sys
import math
import numpy as np
import itertools
from PIL import Image
from pathlib import Path
from scipy import signal
from PIL import Image
from Stegan import Encode, Decode
import math

quant = np.array([[16, 11, 10, 16, 24, 40, 51, 61],  # QUANTIZATION TABLE
                  [12, 12, 14, 19, 26, 58, 60, 55],  # required for DCT
                  [14, 13, 16, 24, 40, 57, 69, 56],
                  [14, 17, 22, 29, 51, 87, 80, 62],
                  [18, 22, 37, 56, 68, 109, 103, 77],
                  [24, 35, 55, 64, 81, 104, 113, 92],
                  [49, 64, 78, 87, 103, 121, 120, 101],
                  [72, 92, 95, 98, 112, 100, 103, 99]])






import random

letter = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p",
          "q","r","s","t","u","v","w","x","y","z",",",".","!","?"," ","0","1"
            ,"2","3","4","5","6","7","8","9"]
number = ["01","02","03","04","05","06","07","08","09","10","11","12","13",
          "14","15","16","17","18","19","20","21","22","23","24","25","26"
    ,"27","28","29","30","31","32","33","34","35","36","37","38","39","40","41"]
def cipher(num,e):
    for i in range(len(num)):
        X.append((int(num[i])**e)%n)
def decipher(num,d):
    for i in range(len(num)):
        Y.append((int(num[i])**d)%n)
def gcd(a, b):
    while b != 0:
        (a, b)=(b, a % b)
    return a
def phi(n):
    amount = 0
    for k in range(1, n + 1):
        if math.gcd(n, k) == 1:
            amount += 1
    return amount

def Decrypt(encoded_image_file):
    global i, j, Y
    Y = []
    hidden_text = Decode(encoded_image_file)
    print("the hidden text \n",hidden_text)
    decipher(hidden_text, d)
    numD = []
    for i in range(len(Y)):
        for j in range(len(number)):
            if(Y[i] == int(number[j])):
                numD.append(letter[j])
    return ''.join(numD)


def Encrypt(original_image_file, plaintext):
# encrypts a plaintext message using the current key
    global numC, j, X
    X = []
    plaintext = (plaintext.lower())
    numC = []
    for i in range(len(plaintext)):
        for j in range(len(letter)):
            if(plaintext[i] == letter[j]):
                numC.append(number[j])
    cipher(numC, e)
    print("Ciphertext:", X)
    img_encoded = Encode(original_image_file, plaintext, X)
    return img_encoded

n = 2537
e = 13
d = 937



class DCT():
    def __init__(self):  # Constructor
        self.message = None
        self.bitMess = None
        self.oriCol = 0
        self.oriRow = 0
        self.numBits = 0
        # encoding part :

    def encode_image(self, img, secret_msg):
        # show(img)
        secret = secret_msg
        self.message = str(len(secret)) + '*' + secret
        self.bitMess = self.toBits()
        # get size of image in pixels
        row, col = img.shape[:2]
        ##col, row = img.size
        self.oriRow, self.oriCol = row, col
        if ((col / 8) * (row / 8) < len(secret)):
            print("Error: Message too large to encode in image")
            return False
        # make divisible by 8x8
        if row % 8 != 0 or col % 8 != 0:
            img = self.addPadd(img, row, col)

        row, col = img.shape[:2]
        ##col, row = img.size
        # split image into RGB channels
        bImg, gImg, rImg = cv2.split(img)
        # message to be hid in blue channel so converted to type float32 for dct function
        bImg = np.float32(bImg)
        # break into 8x8 blocks
        imgBlocks = [np.round(bImg[j:j + 8, i:i + 8] - 128) for (j, i) in itertools.product(range(0, row, 8),
                                                                                            range(0, col, 8))]
        # Blocks are run through DCT function
        dctBlocks = [np.round(cv2.dct(img_Block)) for img_Block in imgBlocks]
        # blocks then run through quantization table
        quantizedDCT = [np.round(dct_Block / quant) for dct_Block in dctBlocks]
        # set LSB in DC value corresponding bit of message
        messIndex = 0
        letterIndex = 0
        for quantizedBlock in quantizedDCT:
            # find LSB in DC coeff and replace with message bit
            DC = quantizedBlock[0][0]
            DC = np.uint8(DC)
            DC = np.unpackbits(DC)
            DC[7] = self.bitMess[messIndex][letterIndex]
            DC = np.packbits(DC)
            DC = np.float32(DC)
            DC = DC - 255
            quantizedBlock[0][0] = DC
            letterIndex = letterIndex + 1
            if letterIndex == 8:
                letterIndex = 0
                messIndex = messIndex + 1
                if messIndex == len(self.message):
                    break
        # blocks run inversely through quantization table
        sImgBlocks = [quantizedBlock * quant + 128 for quantizedBlock in quantizedDCT]
        # blocks run through inverse DCT
        # sImgBlocks = [cv2.idct(B)+128 for B in quantizedDCT]
        # puts the new image back together
        sImg = []
        for chunkRowBlocks in self.chunks(sImgBlocks, col / 8):
            for rowBlockNum in range(8):
                for block in chunkRowBlocks:
                    sImg.extend(block[rowBlockNum])
        sImg = np.array(sImg).reshape(row, col)
        # converted from type float32
        sImg = np.uint8(sImg)
        # show(sImg)
        sImg = cv2.merge((sImg, gImg, rImg))
        return sImg, secret_msg

    # decoding part :
    def decode_image(self, img):
        row, col = img.shape[:2]
        messSize = None
        messageBits = []
        buff = 0
        # split image into RGB channels
        bImg, gImg, rImg = cv2.split(img)
        # message hid in blue channel so converted to type float32 for dct function
        bImg = np.float32(bImg)
        # break into 8x8 blocks
        imgBlocks = [bImg[j:j + 8, i:i + 8] - 128 for (j, i) in itertools.product(range(0, row, 8),
                                                                                  range(0, col, 8))]
        # blocks run through quantization table
        # quantizedDCT = [dct_Block/ (quant) for dct_Block in dctBlocks]
        quantizedDCT = [img_Block / quant for img_Block in imgBlocks]
        i = 0
        # message extracted from LSB of DC coeff
        for quantizedBlock in quantizedDCT:
            DC = quantizedBlock[0][0]
            DC = np.uint8(DC)
            DC = np.unpackbits(DC)
            if DC[7] == 1:
                buff += (0 & 1) << (7 - i)
            elif DC[7] == 0:
                buff += (1 & 1) << (7 - i)
            i = 1 + i
            if i == 8:
                messageBits.append(chr(buff))
                buff = 0
                i = 0
                if messageBits[-1] == '*' and messSize is None:
                    try:
                        messSize = int(''.join(messageBits[:-1]))
                    except:
                        pass
            if len(messageBits) - len(str(messSize)) - 1 == messSize:
                return ''.join(messageBits)[len(str(messSize)) + 1:]
        # blocks run inversely through quantization table
        sImgBlocks = [quantizedBlock * quant + 128 for quantizedBlock in quantizedDCT]
        # blocks run through inverse DCT
        # sImgBlocks = [cv2.idct(B)+128 for B in quantizedDCT]
        # puts the new image back together
        sImg = []
        for chunkRowBlocks in self.chunks(sImgBlocks, col / 8):
            for rowBlockNum in range(8):
                for block in chunkRowBlocks:
                    sImg.extend(block[rowBlockNum])
        sImg = np.array(sImg).reshape(row, col)
        # converted from type float32
        sImg = np.uint8(sImg)
        sImg = cv2.merge((sImg, gImg, rImg))
        ##sImg.save(img)
        # dct_decoded_image_file = "dct_" + original_image_file
        # cv2.imwrite(dct_decoded_image_file,sImg)
        return ''

    """Helper function to 'stitch' new image back together"""

    def chunks(self, l, n):
        m = int(n)
        for i in range(0, len(l), m):
            yield l[i:i + m]

    def addPadd(self, img, row, col):
        img = cv2.resize(img, (col + (8 - col % 8), row + (8 - row % 8)))
        return img

    def toBits(self):
        bits = []
        for char in self.message:
            binval = bin(ord(char))[2:].rjust(8, '0')
            bits.append(binval)
        self.numBits = bin(len(bits))[2:].rjust(8, '0')
        return bits



def ternary(n):
    e = n//3
    q = n%3
    if n == 0:
        return 0
    elif e == 0:
        return q
    else:
        return ternary(e) + q

def binaryToDecimal(binary):
    binary1 = binary
    decimal, i, n = 0, 0, 0
    while (binary != 0):
        dec = binary % 10
        decimal = decimal + dec * pow(2, i)
        binary = binary // 10
        i += 1
    return decimal

def to_bin(data):
    """Convert `data` to binary format as string"""
    if isinstance(data, str):
        return int(''.join([ format(ord(i), "08b") for i in data ]))
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [ format(i, "08b") for i in data ]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return int(format(data, "08b"))
    else:
        raise TypeError("Type not supported.")

class LSB():
    def encode(image_name, secret_data):
        # read the image
        image = cv2.imread (image_name)
        # maximum bytes to encode
        n_bytes = image.shape[0] * image.shape[1] * 3 // 8
        print ("[*] Maximum bytes to encode:", n_bytes)
        if len (secret_data) > n_bytes:
            raise ValueError ("[!] Insufficient bytes, need bigger image or less data.")
        print ("[*] Encoding data...")
        # add stopping criteria
        secret_data += "====="
        data_index = 0
        # convert data to binary
        binary_secret_data = ternary(binaryToDecimal(to_bin (secret_data)))
        # size of data to hide
        print (binary_secret_data)
        data_len = len (binary_secret_data)
        for row in image:
            for pixel in row:
                # convert RGB values to binary format
                r, g, b = to_bin (pixel)
                # modify the least significant bit only if there is still data to store
                if data_index < data_len:
                    # least significant red pixel bit
                    pixel[0] = int (r[:-1] + binary_secret_data[data_index], 3)
                    data_index += 1
                if data_index < data_len:
                    # least significant green pixel bit
                    pixel[1] = int (g[:-1] + binary_secret_data[data_index], 3)
                    data_index += 1
                if data_index < data_len:
                    # least significant blue pixel bit
                    pixel[2] = int (b[:-1] + binary_secret_data[data_index], 3)
                    data_index += 1
                # if data is encoded, just break out of the loop
                if data_index >= data_len:
                    break
        return image

    def decode(image_name):
        print ("[+] Decoding...")
        # read the image

        print ("*")
        print (type (image_name))
        print ("*")

        print ("___")
        binary_data = ""
        for row in image_name:
            for pixel in row:
                r, g, b = dec_to_bin(convertToDecimal (pixel))
                binary_data += r[-1]
                binary_data += g[-1]
                binary_data += b[-1]
        # split by 8-bits
        all_bytes = [binary_data[i: i + 8] for i in range (0, len (binary_data), 8)]
        # convert from bits to characters

        decoded_data = ""
        for byte in all_bytes:
            # decoded_data += byte
            decoded_data += chr (int (byte, 2))
            if decoded_data[-5:] == "=====":
                break
        return decoded_data[:-5]


class Compare():
    def correlation(self, img1, img2):
        return signal.correlate2d(img1, img2)

    def meanSquareError(self, img1, img2):
        error = np.sum((img1.astype('float') - img2.astype('float')) ** 2)
        error /= float(img1.shape[0] * img1.shape[1]);
        return error

    def psnr(self, img1, img2):
        mse = self.meanSquareError(img1, img2)
        if mse == 0:
            return 100
        PIXEL_MAX = 255.0
        return 20 * math.log10(PIXEL_MAX / math.sqrt(mse))

    def ssim(self, img1, img2):
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        kernel = cv2.getGaussianKernel(11, 1.5)
        window = np.outer(kernel, kernel.transpose())

        mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid
        mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
        sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
        sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) *
                                                                (sigma1_sq + sigma2_sq + C2))
        return ssim_map.mean()




# driver part :
# deleting previous folders :
if os.path.exists("Encoded_image/"):
    shutil.rmtree("Encoded_image/")
if os.path.exists("Decoded_output/"):
    shutil.rmtree("Decoded_output/")
if os.path.exists("Comparison_result/"):
    shutil.rmtree("Comparison_result/")
# creating new folders :
os.makedirs("Encoded_image/")
os.makedirs("Decoded_output/")
os.makedirs("Comparison_result/")
original_image_file = ""  # to make the file name global variable
lsb_encoded_image_file = ""
dct_encoded_image_file = ""
dwt_encoded_image_file = ""

while True:
    m = input("To encode press '1', to decode press '2', to compare press '3', press any other button to close: ")

    if m == "1":
        os.chdir("Original_image/")
        original_image_file = input("Enter the name of the file with extension : ")
        dct_img = cv2.imread(original_image_file, cv2.IMREAD_UNCHANGED)
        secret_msg = input("Enter the message you want to hide: ")
        print("The message length is: ", len(secret_msg))
        os.chdir("..")
        os.chdir("Encoded_image/")
        dct_img_encoded, msg = DCT().encode_image(dct_img, secret_msg)
        dct_encoded_image_file = "dct_" + original_image_file
        cv2.imwrite(dct_encoded_image_file, dct_img_encoded)
        lsb_img = Image.open(dct_encoded_image_file)
        lsb_img_encoded = Encrypt(lsb_img, msg)
        lsb_encoded_image_file = "lsb_" + original_image_file
        lsb_img_encoded.save(lsb_encoded_image_file)
        print("Encoded images were saved!")
        os.chdir("..")

    elif m == "2":
        os.chdir("Encoded_image/")
        lsb_img = Image.open(lsb_encoded_image_file)
        os.chdir("..")  # going back to parent directory
        os.chdir("Decoded_output/")
        lsb_hidden_text = Decrypt(lsb_img)
        file = open("lsb_hidden_text.txt", "w")
        file.write(lsb_hidden_text)  # saving hidden text as text file
        file.close()
        print("Hidden texts were saved as text file!")
        os.chdir("..")
    elif m == "3":
        # comparison calls
        os.chdir("Original_image/")
        original = cv2.imread(original_image_file)
        os.chdir("..")
        os.chdir("Encoded_image/")
        lsbEncoded = cv2.imread(lsb_encoded_image_file)
        original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        lsb_encoded_img = cv2.cvtColor(lsbEncoded, cv2.COLOR_BGR2RGB)
        os.chdir("..")
        os.chdir("Comparison_result/")

        book = xlwt.Workbook()
        sheet1 = book.add_sheet("Sheet 1")
        style_string = "font: bold on , color red; borders: bottom dashed"
        style = xlwt.easyxf(style_string)
        sheet1.write(0, 0, "Original vs", style=style)
        sheet1.write(0, 1, "SSIM", style=style)
        sheet1.write(0, 2, "PSNR", style=style)
        sheet1.write(1, 0, "Encoded")
        sheet1.write(1, 1, Compare().ssim(original, lsb_encoded_img))
        sheet1.write(1, 2, Compare().psnr(original, lsb_encoded_img))
        book.save("Comparison.xls")
        print("Comparison Results were saved as xls file!")
        os.chdir("..")
    else:
        print("Closed!")
        break