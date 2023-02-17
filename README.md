# x-stitch

### Aim
Work in progress! Aim is to have an end to end pipeline that takes an image and some parameters to return a cross stitch pattern.  

### What this repo will currently do
So far, the script will run from terminal to return a pattern-looking thing. So it looks like we are close... but the devil is in the detail. 

Take this portrait of a modern day legend as an example:

![bob.jpg](img2xstitch%2Ftest_inputs%2Fbob.jpg)

Putting this through the script with the default params currently returns this:

![bob.jpg](img2xstitch%2Ftest_outputs%2Fbob.jpg)

Not too shabby, but it gets shabbier when you use real life photographs. Take this photo of some flowers (+ some sharpening):

![sunflowers.jpg](img2xstitch%2Ftest_inputs%2Fsunflowers.jpg)

Which then looks like this:

![sunflowers.jpg](img2xstitch%2Ftest_outputs%2Fsunflowers.jpg)

Not the best. Need to work out why the current color quantization process is deciding brown is optimal for the leaves here... 

### What I am working towards
Things I will do (but haven't done yet):

 - Introduce further image preprocessing. Currently, I sharpen the edges which has had a great impact, but I am considering something even more impactful. 
   - The main challenge currently comes from converting photographs - how can we accentuate the intricate features in these images that may perhaps be blending into the background? TBC.
 - Am I happy with the color quantization? Maybe..
 - Add a key to the pattern to identify each symbol:color pair
 - Return the output as a pdf
 - Slap a GUI in front of the script (streamlit looks promising for this)
 - Return required quantities for each thread (this is helpful for bigger pieces)