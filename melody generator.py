import tensorflow.keras as keras
import numpy as np
import json
import music21 as m21
from preprocessing import SEQUENCE_LENGTH, MAPPING_PATH



class MelodyGenerator:

    def  __init__(self, model_path="model.h5"):

        self.model_path = model_path
        self.model = keras.models.load_model(model_path)

        with open(MAPPING_PATH, "r") as fp:
            self._mappings =  json.load(fp)

        self._start_symbols = ["/"] * SEQUENCE_LENGTH

    def generate_melody(self, seed, num_steps, max_sequence_length, temperature):

        #create seed with start symbol
        seed = seed.split()
        melody = seed
        seed =self._start_symbols + seed

        #map seed to int
        seed = [self._mappings[symbol] for symbol in seed]
        
        for _ in range(num_steps):

            #limit the seed to max sequence length
            seed = seed[-max_sequence_length:]

            #one hot encode seed

            onehot_seed = keras.utils.to_categorical(seed, num_classes=len(self._mappings))
            
            #
            onehot_seed = onehot_seed[np.newaxis, ...]

            # make predictions
            probabilitites = self.model.predict(onehot_seed)[0]
            output_int = self._sample_with_temperature(probabilitites, temperature)

            #update the seed
            seed.append(output_int)

            #map int to our encoding
            output_symbol = [k for k, v in self._mappings.items() if v == output_int][0]

            # check whether we are at the end of a melody
            if output_symbol == "/":
                break

            #update the melody
            melody.append(output_symbol)

        return melody




    def _sample_with_temperature(self, probabilites, temperature):

        predictions = np.log(probabilites) / temperature
        probabilites = np.exp(predictions) / np.sum(np.exp(predictions))
        
        choices = range(len(probabilites)) 
        index = np.random.choice(choices, p=probabilites)

        return index


    def save_melody(self, melody, step_duration=0.25, format ="midi", file_name="mel.midi" ):

        # create a music21 stream
        stream = m21.stream.Stream()

        #parse all the symbols in the melody
        start_symbol = None
        Step_counter = 1
        for i, symbol in enumerate(melody):
            #hancle case in which we have a note/rest
            if symbol != "_" or i+1 ==len(melody):
                #ensure we ar dealing with symbol/rest beyond the first one
                if start_symbol is not None:

                    quarter_length_duration = step_duration * Step_counter
                    #handle rest
                    if start_symbol == "r":
                        m21_event = m21.note.Rest(quarterLength = quarter_length_duration)


                    #handle note
                    else:
                        m21_event = m21.note.Note(int(start_symbol), quarterLength = quarter_length_duration)

                    stream.append(m21_event)

                    #reset the step counter
                    Step_counter = 1

                start_symbol = symbol


            #handle other
            else:
                Step_counter += 1 

        stream.write(format, file_name)



    
if __name__ == "__main__":
    mg = MelodyGenerator()
    seed = "60 64 67 _ _ 64 65 _ _ 62 64 62"
    melody = mg.generate_melody(seed, 500, SEQUENCE_LENGTH, 0.9)
    print(seed)
    print(melody)
    mg.save_melody(melody)

