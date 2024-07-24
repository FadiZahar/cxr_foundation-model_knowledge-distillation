from pytorch_lightning.callbacks import Callback
import csv



class MetricLoggingCallback(Callback):
    def __init__(self, filename):
        self.filename = filename
        # Open the file in write mode to initialise and write headers
        with open(self.filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Epoch', 'Batch', 'Validation Loss'])

    def on_validation_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        # Retrieve validation loss from outputs if your validation step returns this
        val_loss = outputs['val_loss'].item() if 'val_loss' in outputs else None
        epoch = trainer.current_epoch
        # Append the epoch, batch index, and validation loss to the file
        with open(self.filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([epoch, batch_idx, val_loss])



            