from facenet_pytorch import MTCNN, InceptionResnetV1, fixed_image_standardization
import torch
from torch.utils.data import DataLoader, SequentialSampler
from torchvision import datasets, transforms
import numpy as np
import os
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix, accuracy_score, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm

# Set device
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print('Running on device: {}'.format(device))

# Load pretrained model
resnet = InceptionResnetV1(
    classify=False,
    pretrained='vggface2'
).to(device)

# Define data transforms
trans = transforms.Compose([
    np.float32,
    transforms.ToTensor(),
    fixed_image_standardization
])

# Load dataset
data_dir = 'Image_dataset_cropped'  # Your cropped images directory
dataset = datasets.ImageFolder(data_dir, transform=trans)
print(f"Found {len(dataset)} images in {len(dataset.classes)} classes")

# Create data loader
batch_size = 32
workers = 0 if os.name == 'nt' else 8
loader = DataLoader(
    dataset,
    num_workers=workers,
    batch_size=batch_size,
    sampler=SequentialSampler(dataset)
)

# Extract embeddings
embeddings = []
labels = []
resnet.eval()
print("Extracting embeddings...")
with torch.no_grad():
    for xb, yb in tqdm(loader):
        xb = xb.to(device)
        b_embeddings = resnet(xb)
        b_embeddings = b_embeddings.to('cpu').numpy()
        embeddings.extend(b_embeddings)
        labels.extend(yb.numpy())

embeddings = np.array(embeddings)
labels = np.array(labels)

# Calculate metrics for each class
print("\nCalculating metrics for each class...")
class_metrics = {}
for class_idx in range(len(dataset.classes)):
    class_name = dataset.classes[class_idx]
    class_mask = labels == class_idx

    # Get embeddings for this class
    class_embeddings = embeddings[class_mask]

    # Calculate mean embedding for this class
    mean_embedding = np.mean(class_embeddings, axis=0)

    # Calculate distances to mean embedding
    distances = np.sum(np.square(class_embeddings - mean_embedding), axis=1)

    # Set threshold
    threshold = np.mean(distances) + np.std(distances)

    # Calculate predictions
    predictions = distances < threshold

    # Calculate metrics
    true_labels = np.ones_like(predictions)  # All should be positive for same class
    accuracy = accuracy_score(true_labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(true_labels, predictions, average='binary')

    class_metrics[class_name] = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }

# Print metrics for each class
print("\nMetrics per class:")
print("-" * 80)
print(f"{'Class':<20} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1-Score':<10}")
print("-" * 80)
for class_name, metrics in class_metrics.items():
    print(
        f"{class_name:<20} {metrics['accuracy']:.4f} {metrics['precision']:.4f} {metrics['recall']:.4f} {metrics['f1_score']:.4f}")

# Calculate overall metrics
overall_accuracy = np.mean([m['accuracy'] for m in class_metrics.values()])
overall_precision = np.mean([m['precision'] for m in class_metrics.values()])
overall_recall = np.mean([m['recall'] for m in class_metrics.values()])
overall_f1 = np.mean([m['f1_score'] for m in class_metrics.values()])

print("\nOverall metrics (average per class):")
print(f"Accuracy: {overall_accuracy:.4f}")
print(f"Precision: {overall_precision:.4f}")
print(f"Recall: {overall_recall:.4f}")
print(f"F1-score: {overall_f1:.4f}")

# ====== NEW: Macro & Weighted Average Metrics ======
print("\nCalculating macro and weighted average metrics...")

# Step 1: Compute class mean embeddings
class_means = []
for class_idx in range(len(dataset.classes)):
    class_embeddings = embeddings[labels == class_idx]
    class_mean = np.mean(class_embeddings, axis=0)
    class_means.append(class_mean)
class_means = np.array(class_means)

# Step 2: Predict label for each sample
predicted_labels = []
for emb in embeddings:
    dists = np.sum((class_means - emb) ** 2, axis=1)  # Euclidean
    pred_label = np.argmin(dists)
    predicted_labels.append(pred_label)

y_true = labels
y_pred = np.array(predicted_labels)

# Step 3: Classification report
print("\nClassification Report (Macro & Weighted Average):")
report = classification_report(y_true, y_pred, target_names=dataset.classes, digits=4)
print(report)

# ====== Confusion Matrix for Sample of Classes ======
n_classes = min(10, len(dataset.classes))
sample_classes = np.random.choice(len(dataset.classes), n_classes, replace=False)
sample_mask = np.isin(labels, sample_classes)
sample_labels = labels[sample_mask]
sample_embeddings = embeddings[sample_mask]

# Calculate pairwise distances
n_samples = len(sample_embeddings)
distances = np.zeros((n_samples, n_samples))
for i in tqdm(range(n_samples), desc="Calculating confusion matrix"):
    for j in range(n_samples):
        diff = np.subtract(sample_embeddings[i], sample_embeddings[j])
        distances[i, j] = np.sum(np.square(diff))

# Predict similarity
threshold = np.mean(distances) + np.std(distances)
predictions = distances < threshold

# Create confusion matrix
true_labels = sample_labels[:, np.newaxis] == sample_labels[np.newaxis, :]
cm = confusion_matrix(true_labels.flatten(), predictions.flatten())

# Plot confusion matrix
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix (Sample of Classes)')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')
plt.savefig('confusion_matrix.png')
plt.close()
