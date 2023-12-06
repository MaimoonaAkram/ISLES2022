import os
import sys
import json
import shutil
import argparse
import numpy as np
from glob import glob
import SimpleITK as sitk

def json_writer(json_path, data):
    with open(str(json_path), "w") as f:
        json.dump(data, f)


class ISLES22():
    def __init__(self, root):
        self.root  = root
        self.data_dict = {}

    def load_data(self):
        dwi_folder    = 'dwi-brain-mri'
        adc_folder    = 'adc-brain-mri'
        flair_folder  = 'flair-brain-mri'

        self.dwi_path   = glob(os.path.join(self.root, dwi_folder, '*.mha'))[0]
        self.adc_path   = glob(os.path.join(self.root, adc_folder, '*.mha'))[0]
        self.flair_path = glob(os.path.join(self.root, flair_folder, '*.mha'))[0]

def reimplement_resize(image_file, target_file, resample_method=sitk.sitkLinear):
    """
    Respacing file to target space size
    :param image_file: sitk.SimpleITK.Image
    :param target_spacing: np.array([H_space, W_space, D_space])
    :resample_method: SimpleITK resample method (e.g. SimpleITK.sitkLinear, SimpleITK.sitkNearestNeighbor)
    :return: resampled_image_file: sitk.SimpleITK.Image
    """
    # pdb.set_trace()
    if isinstance(image_file, str):
        image_file = sitk.ReadImage(image_file)
    elif isinstance(image_file, np.ndarray):
        image_file = sitk.GetImageFromArray(image_file)
    elif type(image_file) is not sitk.SimpleITK.Image:
        assert False, "Unknown data type to respaceing!"
    
    if isinstance(target_file, str):
        target_file = sitk.ReadImage(target_file)
    elif type(target_file) is not sitk.SimpleITK.Image:
        assert False, "Unknown data type to respaceing!"



    # set target size
    target_origing   = target_file.GetOrigin()
    target_direction = target_file.GetDirection()
    target_spacing   = target_file.GetSpacing()
    target_size      = target_file.GetSize()

    # pdb.set_trace()
    # initialize resampler
    resampler_image = sitk.ResampleImageFilter()
    # set the parameters of image
    resampler_image.SetReferenceImage(image_file)  # set rasampled image meta data same to origin data
    resampler_image.SetOutputOrigin(target_origing)
    resampler_image.SetOutputDirection(target_direction)  # set target image space
    resampler_image.SetOutputSpacing(target_spacing)  # set target image space
    resampler_image.SetSize(target_size)  # set target image size
    if resample_method == sitk.sitkNearestNeighbor:
        resampler_image.SetOutputPixelType(sitk.sitkUInt8)
    else:
        resampler_image.SetOutputPixelType(sitk.sitkFloat32)
    resampler_image.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler_image.SetInterpolator(resample_method)

    # launch the resampler
    resampled_image_file = resampler_image.Execute(image_file)
    # pdb.set_trace()

    return resampled_image_file

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_folder', help="root_path of 5 folds", required=True)
    parser.add_argument('-o', "--output_folder", required=True, help="folder for saving evaluation csv")
    args = parser.parse_args()

    input_folder  = args.input_folder
    output_folder = args.output_folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # load origin mha file path
    raw_data_dir = '/input/images'
    dataset_ISLES22 = ISLES22(raw_data_dir)
    dataset_ISLES22.load_data()

    # load mha image
    image_file = sitk.ReadImage(dataset_ISLES22.dwi_path)

    # load prediction
    try:
        pred_file = glob(os.path.join(input_folder, '*.mha'))[0]
        pred_image = sitk.ReadImage(pred_file)
    except:
        print('no prediction! generating full 0 mask!')
        image_array = sitk.GetArrayFromImage(image_file)
        pred_array  = np.zeros_like(image_array)
        pred_image  = sitk.GetImageFromArray(pred_array)

    pred_image.SetOrigin(image_file.GetOrigin())
    pred_image.SetSpacing(image_file.GetSpacing())
    pred_image.SetDirection(image_file.GetDirection())

    sitk.WriteImage(pred_image, os.path.join(output_folder, dataset_ISLES22.dwi_path.split('/')[-1]))

    # dump the result to json file
    case_results = []
    json_result =   {"outputs": [dict(
                                    type="Image", 
                                    slug="stroke-lesion-segmentation",
                                    filename=str(dataset_ISLES22.dwi_path.split('/')[-1]))],
                    "inputs": [dict(
                                    type="Image", 
                                    slug="dwi-brain-mri",
                                    filename=str(dataset_ISLES22.dwi_path.split('/')[-1]))]}
    case_results.append(json_result)
    json_writer(os.path.join(output_folder, 'result.json'), case_results)
