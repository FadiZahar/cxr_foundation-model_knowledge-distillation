# Configuration for project-wide settings

# Model Parameters
IMAGE_SIZE = (224, 224)
CXRFM_EMBEDS_SIZE = 1376
NUM_CLASSES = 14

# Training
EPOCHS = 20
NUM_WORKERS = 4
BATCH_SIZE = 150
LEARNING_RATE = 0.001

# Data Paths
CXRS_FILEPATH = '/vol/biodata/data/chest_xray/CheXpert-v1.0/'
EMBEDDINGS_FILEPATH = '/vol/biomedic3/bglocker/mscproj24/fz221/data/cxrfm_embeddings/chexpert/cxr_numpy'
TRAIN_RECORDS_CSV = '/vol/biodata/data/chest_xray/CheXpert-v1.0/meta/algorithmic_encoding/chexpert.sample.train.csv'
VAL_RECORDS_CSV = '/vol/biodata/data/chest_xray/CheXpert-v1.0/meta/algorithmic_encoding/chexpert.sample.val.csv'
TEST_RECORDS_CSV = '/vol/biodata/data/chest_xray/CheXpert-v1.0/meta/algorithmic_encoding/chexpert.sample.test.csv'
MAIN_DIR_PATH = '/vol/biomedic3/bglocker/mscproj24/fz221/outputs/'