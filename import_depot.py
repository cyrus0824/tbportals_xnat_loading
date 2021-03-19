import xnat
import pickle
import datetime
import os
import json

def get_image_file_from_list(l):
    for fn in l:
        if fn == 'dcm_metadata' or fn == 'dcm_full_metadata':
            continue
        else:
            return fn
    return None

session = xnat.connect('https://bcbbxnat-dev.niaid.nih.gov')

# Get depot metadata
with open('full_dcm_metadata_aggregated_by_patient.pickle', 'rb') as inf:
    patients = pickle.load(inf)

# get project
cyrus_test_project = session.projects["cyrus_test"]

# create subjects (assumes project is already created - in this case cyrus_test_project)
for patient in patients.keys():
    _s = session.classes.SubjectData(parent=cyrus_test_project, label=patient)

print("Created SubjectData")

os.chdir('/Users/afrasiabic2/code/xnat/output')
for (i, (_dir, _dirs, _files)) in enumerate(list(os.walk('.'))[1:]):
    print(f"Starting image number {i} in directory {_dir}. . .")
    os.chdir(_dir)
    image_file = get_image_file_from_list(_files)
    if not image_file:
        os.chdir('..')
        continue
    if os.path.exists(os.path.abspath('dcm_full_metadata')):
        with open('dcm_full_metadata', 'r') as inf:
            try:
                image_metadata = json.load(inf)
            except:
                os.chdir('..')
                continue
        if image_metadata and 'studies' in image_metadata:
            try:
                patient_id = image_metadata['studies'][0]['PatientID']
                subject = cyrus_test_project.subjects[patient_id]
                study_date = datetime.datetime.strptime(image_metadata['studies'][0]['Study Date'], '%m/%d/%Y')
                dcm_patient_id = image_metadata['studies'][0]['PatientID']
                modality = image_metadata['studies'][0]['series'][0]['Modality']
                uid = image_metadata['studies'][0]['StudyInstanceUID']
                scan_uid = image_metadata['studies'][0]['series'][0]['instances'][0]['metadata']['SOPInstanceUID']
                exp_label = f'Exp{i}'
                scan_label = f'Scan{i}'
                #print(f"{patient_id}\t{subject}\t{study_date}\t{dcm_patient_id}\t{modality}\t{uid}\t{scan_uid}\t{exp_label}\t{scan_label}") 
                # create the session data for this experiment
                cr_session = session.classes.CrSessionData(date = study_date.date(), 
                                                       parent = subject,
                                                       label = exp_label, 
                                                       uid = uid, 
                                                       dcm_patient_id = dcm_patient_id,
                                                       modality = modality)
            
                # create the scan for this experiment
                scan = session.classes.CrScanData(parent = cr_session,
                                              label = scan_label,
                                              uid = scan_uid)
                # upload the image
                _cr_session = session.services.import_(path=os.path.abspath(image_file), 
                                                       project='cyrus_depot',
                                                       subject=subject.id,
                                                       experiment = exp_label,
                                                       overwrite="delete")
                print(f"Created CrSession {cr_session}, CrScan {scan}, image {image_file}")
            except:
                pass
    os.chdir('..')

