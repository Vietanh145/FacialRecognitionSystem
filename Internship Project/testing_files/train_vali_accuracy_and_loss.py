import matplotlib.pyplot as plt

# Data extracted from the output from finetune.ipynb
epochs = list(range(1, 21))  # Epochs 1 to 20
train_acc = [0.4488, 0.7393, 0.8182, 0.8629, 0.8933, 0.9614, 0.9806, 0.9878, 0.9925, 0.9953,
             0.9974, 0.9981, 0.9982, 0.9984, 0.9987, 0.9989, 0.9992, 0.9994, 0.9992, 0.9993]
valid_acc = [0.6873, 0.7836, 0.8404, 0.8414, 0.8635, 0.9187, 0.9219, 0.9233, 0.9230, 0.9227,
             0.9248, 0.9250, 0.9249, 0.9253, 0.9263, 0.9257, 0.9255, 0.9263, 0.9247, 0.9254]
train_loss = [2.3134, 1.0137, 0.6904, 0.5116, 0.3860, 0.1463, 0.0796, 0.0520, 0.0350, 0.0236,
              0.0143, 0.0120, 0.0106, 0.0100, 0.0089, 0.0084, 0.0072, 0.0068, 0.0065, 0.0059]
valid_loss = [1.2425, 0.8412, 0.6311, 0.6252, 0.5381, 0.3490, 0.3378, 0.3460, 0.3602, 0.3740,
              0.3645, 0.3695, 0.3636, 0.3712, 0.3699, 0.3725, 0.3691, 0.3707, 0.3742, 0.3732]

# Plot 1: Train and Validation Accuracy
plt.figure(figsize=(10, 6))
plt.plot(epochs, train_acc, label='Train Accuracy', marker='o')
plt.plot(epochs, valid_acc, label='Validation Accuracy', marker='s')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Train and Validation Accuracy Over Epochs')
plt.legend()
plt.grid(True)
plt.savefig('accuracy_plot.png')
plt.close()

# Plot 2: Train and Validation Loss
plt.figure(figsize=(10, 6))
plt.plot(epochs, train_loss, label='Train Loss', marker='o')
plt.plot(epochs, valid_loss, label='Validation Loss', marker='s')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Train and Validation Loss Over Epochs')
plt.legend()
plt.grid(True)
plt.savefig('loss_plot.png')
plt.close()