you are an expert python software engineer, you need to write a python 3.0 script that:
- receives a integer and a folder path as command line parameter
- store the integer in a variable called layer_height
- store the folder path in a variable called png_folder
- checks that in the folder there are only PNG image files and all those files have the same x and y dimensions
- store such x and y dimensions in two variables called png_w and png_h
- create a text file in the current directory called "qdx.qdx", and add to the file the following line "JieHe,LH,4000,8000,2,030,0,FA" replacing "LH" with layer_height 
- create a matrix of bytes 8000 by 4000 called main_img
- create a matrix of bytes 800 by 400 called thumb_img
- create an array of triplets
- once the previous steps are completed, open each file in alphabetic order and perform the following steps from 1 to 7:
	1. write a counter in the qdx file
    2. copy the image centered inside the matrix main_img, black pixels equal zero in the matrix element, non black pixels equal one
    3. copy the image scaled by factor 10 centered inside the matrix thumb_img, scaled down by factor 10, black pixels equal zero in the matrix element, non white pixels equal one
	4. for each column in the matrix thumb_img, follow this set of operations:
		a. count elements from row 1 to row 400
		b. every time the value changes from 0 to 1 or from 1 to 0, if count is not 400, write the following triplet on the qdx file: column,count,value
		c. count is reset to 0 every time you write a line
	5. write "FB" in the file qdx.qdx
	6. for each column in the matrix main_img, follow this set of operations:
		a. count elements from row 1 to row 4000
		b. every time the value changes from 0 to 1 or from 1 to 0, if count is not 400, write the following triplet on the qdx file: column,count,value
		c. count is reset to 0 every time you write a line

	7. write "FC" in the file qdx.qdx
print on screen every step, adding a timestamp with the format HH:MM:SS and describing the operation briefly 
don't use deprecated python methods and attributes
