#include <stdio.h>
#include <stdlib.h>
#include <png.h>

#define WIDTH 8000
#define HEIGHT 4000

int main() {
  // Allocate memory for the image data (8 bits per pixel)
  unsigned char* image_data = (unsigned char*)malloc(WIDTH * HEIGHT * sizeof(unsigned char));
  if (image_data == NULL) {
    fprintf(stderr, "Error allocating memory for image data\n");
    return 1;
  }

  // Initialize image data (set all pixels to black)
  for (int i = 0; i < WIDTH * HEIGHT; ++i) {
    image_data[i] = 0; // Black (0 for grayscale)
  }

  // Create a PNG image structure
  png_structp png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  if (!png_ptr) {
    fprintf(stderr, "Error creating PNG write structure\n");
    free(image_data);
    return 1;
  }

  // Create a PNG info structure
  png_infop info_ptr = png_create_info_struct(png_ptr);
  if (!info_ptr) {
    fprintf(stderr, "Error creating PNG info structure\n");
    png_destroy_write_struct(&png_ptr, (png_infopp)NULL);
    free(image_data);
    return 1;
  }

  // Set PNG info attributes
  png_set_IHDR(png_ptr, info_ptr, WIDTH, HEIGHT, 8, PNG_COLORTYPE_GRAY, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT, PNG_INTENT_TYPE_DEFAULT);

  // Open a PNG file for writing
  FILE *fp = fopen("image.png", "wb");
  if (!fp) {
    fprintf(stderr, "Error opening file for writing\n");
    png_destroy_write_struct(&png_ptr, &info_ptr);
    free(image_data);
    return 1;
  }

  // Initialize PNG writer
  png_init_io(png_ptr, fp);

  // Write PNG header information
  png_write_info(png_ptr, info_ptr);

  // Define how image data is arranged in rows (bytes per row)
  int row_bytes = WIDTH;

  // Write image data row by row
  png_bytepp row_pointers = (png_bytepp)malloc(HEIGHT * sizeof(png_bytep));
  for (int y = 0; y < HEIGHT; y++) {
    row_pointers[y] = &image_data[y * row_bytes];
  }
  png_write_image(png_ptr, row_pointers);

  // End PNG writing and clean up
  png_write_end(png_ptr, info_ptr);
  free(row_pointers);
  fclose(fp);
  png_destroy_write_struct(&png_ptr, &info_ptr);
  free(image_data);

  printf("Image saved as image.png\n");
  return 0;
}
