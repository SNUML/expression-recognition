# Expression-Recognition
#### Preprocessing and recognition training code for processing handwritten mathematical expressions

Dataset: https://www.kaggle.com/rtatman/handwritten-mathematical-expressions

## Preprocessing
#### Code for parsing inkml files into trainable png files
Code is found under `./preprocessing`.
### expression_loader.py
Contains `Expression` class for reading inkml string and parsing attributes.

### symbol_processor.py
Contains functions for handling symbol normalization.
