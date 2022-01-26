import itertools
import os

import music21 as m21

from musif.musicxml.tempo import get_number_of_beats

file_names = []
repeat_bracket = False


def measure_ranges(instrument_measures, init, end, iteration=None, offset=None, twoCompasses=False, remove_repetition_marks = False):
    measures = []
    o = offset
    last_offset = 0.0 if int(init) - 6 < 0 else instrument_measures[int(init) - 6].offset

    #Find index where measureNumber init and end is stored
    init_index = instrument_measures.index([m for m in instrument_measures if m.measureNumber == init][0])
    end_compass = [m for m in instrument_measures if m.measureNumber == end]
    end_index = instrument_measures.index(end_compass[0]) if len(end_compass) > 0 else len(instrument_measures) - 1
    for i in range(init_index, end_index + 1):
        if not i < 0 and i < len(instrument_measures) and instrument_measures[i].measureNumber >= int(init) and instrument_measures[i].measureNumber <= int(end):
            if not twoCompasses:
                compass = instrument_measures[i].quarterLength
                m = m21.stream.Measure(number =instrument_measures[i].measureNumber)
                if remove_repetition_marks:
                    m.elements = [e for e in instrument_measures[i].elements if not isinstance(e, m21.repeat.RepeatMark)]
                else:
                    m.elements = instrument_measures[i].elements 
                m.quarterLength = compass
                if offset is None:
                    m.offset = last_offset
                else:
                    m.offset = o
                    o += compass
                
                measures.append(m)
                if instrument_measures[i].measureNumber != 0.0 and instrument_measures[i].offset != 0:
                    last_offset = instrument_measures[i].offset + compass
            twoCompasses = False
    
    if iteration == 2:
        last_measure = instrument_measures[i + 1]
        last_measure.offset = measures[-1].offset
        measures = measures[:-1] + [last_measure]
    return measures

def get_instrument_elements(part):
    measures = []
    for elem in part:
        if isinstance(elem, m21.stream.Measure):
            measures.append(elem)
            #Change the note offsets to avoid problems due to the slurs
            last_offset = 0
            last_duration = 0
            for note in elem:
                if isinstance(note, m21.note.Note) or isinstance(note, m21.note.Rest) or isinstance(note, m21.chord.Chord):
                    note.offset = last_offset + last_duration
                    last_offset = note.offset
                    last_duration = note.duration.quarterLength
    return measures

def get_repeat_elements(score, v = True):
    global repeat_bracket
    repeat_bracket = False
    # 1. Get the repeat elements
    repeat_elements = set()
    
    for instruments in score.parts:
        instr_repeat_elements = []
        for elem in instruments.elements:
            if isinstance(elem, m21.stream.Measure):
                for e in elem:
                    if isinstance(e, m21.repeat.RepeatMark) and not isinstance(e, m21.bar.Repeat):
                        measure = e.measureNumber
                        if elem.numberSuffix in ['X1', 'X2']: #Exception
                            measure += 1
                        instr_repeat_elements.append((measure, e.name))
            elif isinstance(elem, m21.spanner.RepeatBracket):
                repeat_bracket = True
                string_e = str(elem)
                index = string_e.find("music21.stream.Measure")
                string_e = string_e[index:].replace("music21.stream.Measure ", '')
                measure = string_e.split(' ')[0].strip().replace('X1', '').replace('X2', '')
                instr_repeat_elements.append((int(measure), "repeat bracket" + elem.number))
        repeat_elements.update(instr_repeat_elements)
    
    repeat_elements = sorted(list(repeat_elements), key=lambda tup:tup[0])
    if v: #VERBOSE
        print("The repeat elements found in this score are: " + str(repeat_elements))
    return repeat_elements

def include_beats(harmonic_analysis):
    harmonic_analysis['beats']=0
    for index, measure in enumerate(harmonic_analysis.playthrough):
        if measure<=1:
            # beat = int(measure + float(harmonic_analysis.mn_onset[index])*int(harmonic_analysis.timesig[index][0]))
            beat = int(measure + float(harmonic_analysis.mc_onset[index])*int(harmonic_analysis.timesig[index][0]))

        else:
            # beat = int((measure-1)*int(harmonic_analysis.timesig[index-1][0])+1  + harmonic_analysis.mn_onset[index]*int(harmonic_analysis.timesig[index][0]))
            beat = int((measure-1)*int(harmonic_analysis.timesig[index-1][0])+1  + harmonic_analysis.mc_onset[index]*int(harmonic_analysis.timesig[index][0]))
        
        harmonic_analysis['beats'][index]=beat
        
def get_beat_position(beats_timesignature, number_of_beats, pos):
    if number_of_beats == beats_timesignature:
        return pos
    else:
        return (pos / beats_timesignature) + 1  # It could be better: (pos/beat_count)*beat and changes in dynamics
        
    #TEST this with 3/8
    
def expand_repeat_bars(score):
    final_score = m21.stream.Score()
    final_score.metadata = score.metadata
    exist_repetition_bars = False
    #find repeat bars and expand
    for instr in score.parts:
        part_measures = get_instrument_elements(instr.elements) #returns the measures with repetitions
        last_measure = part_measures[-1].measureNumber
        part_measures_expanded = []
        startsin0 = part_measures[0].measureNumber == 0 #Everything should be -1
        repetition_bars = []

        #Find all repetitions in that instrument
        for elem in instr.elements:
            if isinstance(elem, m21.stream.Measure):
                for e in elem:
                    if isinstance(e, m21.bar.Repeat):
                        exist_repetition_bars = True
                        if e.direction == "start":
                            repetition_bars.append((e.measureNumber, "start"))
                        elif e.direction == "end":
                            repetition_bars.append((e.measureNumber, "end"))
                        index = elem.elements.index(e)
                        elem.elements = elem.elements[:index] + elem.elements[index + 1:]
            elif isinstance(elem, m21.spanner.RepeatBracket):
                string_e = str(elem)
                index = string_e.find("music21.stream.Measure")
                measure = string_e[index:].replace("music21.stream.Measure", '')[1:3].strip()
                repetition_bars.append((int(measure), elem.number))
                index = instr.elements.index(elem)
                elem.elements = instr.elements[:index] + instr.elements[index + 1:]
        repetition_bars = sorted(list(repetition_bars), key=lambda tup:tup[0])

        start = 0 if startsin0 else 1
        if exist_repetition_bars:
            p = m21.stream.Part()
            p.id = instr.id
            p.partName = instr.partName
            for rb in repetition_bars:
                compass = measure_ranges(part_measures, rb[0], rb[0])[0].quarterLength
                if rb[1] == "start":
                    if len(part_measures_expanded) > 0:
                        offset = part_measures_expanded[-1][-1].offset
                    else:
                        offset = 0
                    start_measures = measure_ranges(part_measures, start, rb[0] - 1, offset = offset + compass) #TODO works if the score doesn't start in 0?
                    if len(start_measures) > 0:
                        part_measures_expanded.append(start_measures)
                    start = rb[0]
                elif rb[1] == "end":
                    if len(part_measures_expanded) > 0:
                        offset = part_measures_expanded[-1][-1].offset
                    else:
                        offset = 0
                    casilla_1 = True if any(re[1] == '1' and re[0] <= rb[0] for re in repetition_bars) else False
                    casilla_2 = None
                    if casilla_1:
                        casilla_2 = [re for re in repetition_bars if re[1] == '2' and re[0] > rb[0]]
                        casilla_2 = None if len(casilla_2) == 0 else casilla_2[0] 
                    part_measures_expanded.append(measure_ranges(part_measures, init = start, end = rb[0], offset = offset+ compass, remove_repetition_marks=True)) # This should erase the repetition marks
                    if casilla_2 != None:
                        part_measures_expanded.append(measure_ranges(part_measures, start, casilla_2[0], iteration = 2, offset = part_measures_expanded[-1][-1].offset+ compass))
                        start = casilla_2[0] + 1
                    else:
                        part_measures_expanded.append(measure_ranges(part_measures, init = start, end = rb[0], offset = part_measures_expanded[-1][-1].offset + compass))
                        start = rb[0] + 1
            if start < last_measure:
                compass = measure_ranges(part_measures, start, start + 1)[0].quarterLength
                offset = part_measures_expanded[-1][-1].offset
                part_measures_expanded.append(measure_ranges(part_measures, start, last_measure + 1, offset = offset+ compass)) #TODO works when it's close to the end?

            p.elements = list(itertools.chain(*tuple(part_measures_expanded)))
            final_score.insert(0, p)
        
    return final_score if exist_repetition_bars else score

def get_measure_list(part_measures, repeat_elements):
    measures_list = []
    startsin0 = part_measures[0].measureNumber == 0 #Everything should be -1

    there_is_fine = False
    there_is_segno = False
    #1. find the fine and segno
    if any([r[1] == "fine" for r in repeat_elements]):
        f = [x[0] for x in repeat_elements if x[1] == "fine"][0]
        there_is_fine = True
    if any([r[1] == "segno" for r in repeat_elements]):
        s = [x[0] for x in repeat_elements if x[1] == "segno"][0]
        there_is_segno = True

    #2. Having all the repetition elements, get the measures
    if there_is_segno: #Introduction
        before_segno = measure_ranges(part_measures,1 if not startsin0 else 0, s - 1)
        measures_list.append(before_segno) #S -1 OR S-> when segno in compass 1, s, else s-1?
        dc_time_signature = [y for x in before_segno for y in x.elements if isinstance(y, m21.meter.TimeSignature)]
    elif there_is_fine:
        measures_list.append(measure_ranges(part_measures,1 if not startsin0 else 0, f - 1, iteration = 1 if repeat_bracket else None))
    else:
        measures_list.append(measure_ranges(part_measures,1 if not startsin0 else 0, len(part_measures), iteration = 1 if repeat_bracket else None))

    for repeat in repeat_elements:
        repeat_measure = measure_ranges(part_measures, repeat[0], repeat[0])
        compass = repeat_measure[0].quarterLength

        if repeat[1] == "segno":
            offset = measures_list[-1][-1].offset
            segno_part = measure_ranges(part_measures, s, f - 1 if there_is_fine else len(part_measures), iteration = 1 if repeat_bracket else None, offset = offset + compass, remove_repetition_marks = True)
            measures_list.append(segno_part) # Segno to Fine
        elif repeat[1] == "fine":
            twoCompasses = False
            """if len(repeat_measure) > 0:
                twoCompasses = True"""
            offset = measures_list[-1][-1].offset
            fine_part = measure_ranges(part_measures, f, len(part_measures), offset = offset + compass, twoCompasses=twoCompasses, remove_repetition_marks = True)
            measures_list.append(fine_part) # Fine to end
        elif repeat[1] == "al segno" or repeat[1] == "dal segno":
            offset = measures_list[-1][-1].offset
            # segnos' compass time signature
            segno_time_measure = [x for x in segno_part[0].elements if isinstance(x, m21.meter.TimeSignature)]
            segno_time_measure = segno_time_measure if len(segno_time_measure) != 0 else dc_time_signature[-1]
            alsegno_list = measure_ranges(part_measures, s, f - 1 if there_is_fine else len(part_measures), iteration = 2 if repeat_bracket else None, offset=offset + compass, remove_repetition_marks = True)
            if not any(isinstance(x, m21.meter.TimeSignature) for x in alsegno_list[0].elements):
                #we reset the time signature that was on the dacapo
                alsegno_list[0].elements = tuple([segno_time_measure] + list(alsegno_list[0].elements))
            
            measures_list.append(alsegno_list) # Segno to fine
        elif repeat[1] == "da capo":
            offset = measures_list[-1][-1].offset
            if startsin0 and there_is_fine and not repeat_bracket:
                f += 1
            dacapo_list = measure_ranges(part_measures, 0 if startsin0 else 1, f - 1 if there_is_fine else len(part_measures), iteration = 2 if repeat_bracket else None, offset=offset + compass, remove_repetition_marks = True)
            measures_list.append(dacapo_list)

    return measures_list

def expand_part(part, repeat_elements):
    part_measures = get_instrument_elements(part.elements) #returns the measures with repetitions
    p = m21.stream.Part()
    p.id = part.id
    p.partName = part.partName
    
    part_measures_expanded = get_measure_list(part_measures, repeat_elements) #returns the measures expanded
    part_measures_expanded = list(itertools.chain(*part_measures_expanded))
    #part_measures_expanded = sorted(tuple(part_measures_expanded), key =lambda x: x.offset)
    # Assign a new continuous compass number to every measure
    measure_number = 0 if part_measures_expanded[0].measureNumber == 0 else 1
    for i, e in enumerate(part_measures_expanded):
        m = m21.stream.Measure(number = measure_number)
        m.elements = e.elements
        m.offset  = e.offset
        m.quarterLength = e.quarterLength
        part_measures_expanded[i] = m
        measure_number += 1
    p.elements = part_measures_expanded
    return p
    
def expand_score_repetitions(score, repeat_elements):
    score = expand_repeat_bars(score)  # FIRST EXPAND REPEAT BARS
    final_score = m21.stream.Score()
    final_score.metadata = score.metadata
    
    if len(repeat_elements) > 0:
        for part in score.parts:
            p = expand_part(part, repeat_elements)

            final_score.insert(0, p)
    else:
        final_score = score
    return final_score

def remove_folder_contents(path: str):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            remove_folder_contents(file_path)

def Get_TimeSignature_periods(time_signatures):
    # TODO: Comprobar para cuando haya repeticiones, que al volver usa el beat del compas que toca.
    periods = [0]
    if len(time_signatures) == 0:
        return periods
    for t in range(1, len(time_signatures)):
        if time_signatures[t] != time_signatures[t-1]:
            periods.append(t - periods[-1])  # Substract indexes in case measures are not cointinuous
    periods.append(t - periods[-1])
    
    return periods
    

def calculate_total_number_of_beats(time_signatures, periods):
    return sum([period * get_number_of_beats(time_signatures[j]) for j, period in enumerate(periods)])
