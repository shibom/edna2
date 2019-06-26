#include <iostream>
//#include <hdf5.h>
//#include <hdf5_hl.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <cbf.h>
#include <cbf_simple.h>

#define CHECK_RETURN(x,y){if (x) {printf(y);}};

const int MaxStrLen = 255;


static void trim_line(char *s){
        size_t i;
        if (!s) return;
        for (i = 0; i < strlen(s); i++){
            if ( (s[i] == '\n') || (s[i] == '\r') ) {
                s[i] = '\0';
                return;
            }
        }
}


int load_cbf(cbf_handle &cbfh, int** outArray, int x_pixels, int y_pixels){
    const char * headertype;
    // First, find binary section in cbf
    CHECK_RETURN(cbf_find_category(cbfh, "array_data"), "Finding array_data category");
    CHECK_RETURN(cbf_find_column(cbfh, "data"), "Finding data column");
    CHECK_RETURN(cbf_select_row(cbfh, 0), "Selecting row 0 of data column");
    CHECK_RETURN(cbf_get_typeofvalue(cbfh, &headertype), "Finding binary data");
    if (strcmp(headertype, "bnry") != 0)
        printf("ERROR: Unable to find binary image.\n");

    // a whole bunch of variables needed to get cbf_get_integerarrayparameters_wdims
    unsigned int compression;
    int binId, elSigned, elUnsigned, minEl, maxEl;
    size_t elSize, elements, fs, ss, sss, padding;
    const char * byteOrder;

    CHECK_RETURN(cbf_get_integerarrayparameters_wdims(cbfh, &compression, & binId, & elSize,
        &elSigned, &elUnsigned, &elements, &minEl, &maxEl, &byteOrder, & fs,
        & ss, &sss, &padding), "reading image meta data");

    //int x_pixels = 1475;
    //int y_pixels = 1679;
    size_t elements_read = 0;
    size_t totLen = x_pixels * y_pixels;

    *outArray = new int[totLen];
    int* outArr = *outArray;

    CHECK_RETURN(cbf_get_integerarray(cbfh, &binId, outArr, \
        sizeof(int), 1, elements, &elements_read), "Reading image");

    //for (int i = 0; i < 100; i++){
    //    std::cout << outArr[i] << '\n';
    //}
    return 0;
}
/*
int create_list_from_file(char* filename, char* cbf_lst, size_t numFiles){

    const int MaxStrLen = 255;
    FILE* fList = fopen(filename, "r");
    char line[MaxStrLen];
    numFiles = 0;

    while(!feof(fList)){
        fgets(line, MaxStrLen, fList);
        numFiles++;
    }
    rewind(fList); // set the file index to the start of the file.

    char* cbf_lst = new char[numFiles*MaxStrLen]; // allocate char array in memory for cbf list.
    numFiles = 0;
    while(!feof(fList)){
        fgets(line, MaxStrLen, fList);
        sscanf(line, "%s", line);
        sprintf(&cbf_lst[numFiles*MaxStrLen], "%s\0", line);
        numFiles++;

    }

    fclose(fList);
    for (size_t i = 0; i < numFiles; i++){
        std::cout << &cbf_lst[i*MaxStrLen] << std::endl;
    }
    return 0;
}*/

int** load_from_cbfList(char* lst_of_cbfs, size_t size_of_lst, int* img_dimension){

    const int MaxStrLen = 255;
    //int** buffer = NULL;

    if ( (lst_of_cbfs == NULL) || (size_of_lst == 0) ){
        printf("Provided an empty CBF list");
        //return buffer;
    }

    if (!(img_dimension[0] > 0 && img_dimension[1] > 0)) {
        printf("raw image must be 2D in pixels\n");
        //return buffer;
    }

    size_t img_length = 1;
    for (int i = 0; i < 3; i++) {
        img_length *= img_dimension[i];
    }

    // allocate 2D array as set of pointers of pointers in Memory

    int** buffer = new int*[size_of_lst];

    for (size_t i = 0; i < size_of_lst; i++) {
        buffer[i] = new int[img_length];
    }

    for (size_t frame = 0; frame < size_of_lst; frame++){

        //create empty cbf object
        cbf_handle cbfh;
        CHECK_RETURN(cbf_make_handle(&cbfh), "creating cbf handle");

        //open cbf file using std open method
        char* each_cbf;
        int* data_array = NULL; //output single image array

        each_cbf = &lst_of_cbfs[frame*MaxStrLen];
        trim_line(each_cbf);
        FILE* cbfFH = fopen(each_cbf, "rb");
        if (cbfFH == NULL){
            printf("ERROR: Couldn't open %s\n", each_cbf);
        }

        // populate cbf object by reading from cbf_file_handle
        CHECK_RETURN(cbf_read_widefile(cbfh, cbfFH, MSG_NODIGEST), "reading cbf file");
        load_cbf(cbfh, &data_array, img_dimension[0], img_dimension[1]);
        fclose(cbfFH);


        for (size_t j = 0; j < img_length; j++){
            buffer[frame][j] = data_array[j];
        }
        std::cout << "frame put in: " << frame << std::endl;
        free(data_array);

    }

    return buffer;
}

int main(int argc, const char* argv[]){
    if (argc != 2){
        printf("need cbf filename");
        return 0;
    }
    char fname[1024];
    strcpy(fname, argv[1]);
    //char* cbf_files = NULL;
    //size_t nframes = 0;
    int dim[2] = {1475, 1679};
    //create_list_from_file(fname, &cbf_files, nframes);

    FILE* fList = fopen(fname, "r");
    char str1[MaxStrLen];

    size_t nframes = 0;
    while (!feof(fList)){
        fgets(str1, MaxStrLen, fList);
        nframes++;
    }
    rewind(fList); // set the file index to the start of the file.


    char* cbf_lst = new char[MaxStrLen*nframes];
    nframes = 0;
    while (!feof(fList)){
        fgets(str1, MaxStrLen, fList);
        sscanf(str1, "%s", str1);
        sprintf(&cbf_lst[nframes*MaxStrLen], "%s\0", str1);
        nframes++;
    }
    fclose(fList);

    std::cout << "no. of frames: " << nframes << '\n';

    size_t totLen = dim[0]*dim[1];

    //int buf = **load_from_cbfList(cbf_lst, nframes, dim);
    int** buffer = new int*[nframes];
    for (size_t i = 0; i < nframes; i++){
        buffer[i] = new int[totLen];
    }

    for (size_t frame = 0; frame < nframes; frame++){

        //create empty cbf object
        cbf_handle cbfh;
        CHECK_RETURN(cbf_make_handle(&cbfh), "creating cbf handle");

        //open cbf file using std open method
        char* each_cbf;
        int* data_array = NULL; //output single image array

        each_cbf = &cbf_lst[frame*MaxStrLen];
        trim_line(each_cbf);
        FILE* cbfFH = fopen(each_cbf, "rb");
        if (cbfFH == NULL){
            printf("ERROR: Couldn't open %s\n", each_cbf);
        }

        // populate cbf object by reading from cbf_file_handle
        CHECK_RETURN(cbf_read_widefile(cbfh, cbfFH, MSG_NODIGEST), "reading cbf file");
        load_cbf(cbfh, &data_array, dim[0], dim[1]);
        fclose(cbfFH);


        for (size_t j = 0; j < totLen; j++){
            buffer[frame][j] = data_array[j];
        }
        free(data_array);
    }
    /*



    for (size_t i =0; i < nframes; i++){
        for (size_t j = 0; j < totLen; j++){
            std::cout << buf[i][j] << " ";
        }

        std::cout << std::endl;
    }*/
    return 0;
}



