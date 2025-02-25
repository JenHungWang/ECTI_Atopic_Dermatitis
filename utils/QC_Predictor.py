import torch
from PIL import Image
import torchvision.transforms as transforms
import utils.models_vit as models
from pathlib import Path


class ModelPredictor:
    def __init__(self, checkpoint_path, model_name='RETFound_mae', num_classes=2, input_size=224, device='cuda'):
        """Initialize the predictor with model parameters."""
        self.checkpoint_path = checkpoint_path
        self.model_name = model_name
        self.num_classes = num_classes
        self.input_size = input_size
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model()

    def _load_model(self):
        """Load and initialize the model from checkpoint."""
        model = models.__dict__[self.model_name](
            img_size=self.input_size,
            num_classes=self.num_classes,
            global_pool=True
        )

        checkpoint = torch.load(self.checkpoint_path, map_location='cpu', weights_only=False)
        print(f"Loaded checkpoint from: {self.checkpoint_path}")

        if 'model' in checkpoint:
            checkpoint_model = checkpoint['model']
        elif 'teacher' in checkpoint:
            checkpoint_model = checkpoint['teacher']
        else:
            checkpoint_model = checkpoint

        checkpoint_model = {k.replace("backbone.", ""): v for k, v in checkpoint_model.items()}
        model.load_state_dict(checkpoint_model, strict=False)

        model.to(self.device)
        model.eval()
        return model

    def _preprocess_image(self, image_path):
        """Preprocess the image for model input."""
        transform = transforms.Compose([
            transforms.Resize((self.input_size, self.input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0)
        return image_tensor

    def predict(self, image_path):
        """Perform prediction on a single image and return results."""
        image_tensor = self._preprocess_image(image_path)
        image_tensor = image_tensor.to(self.device)

        with torch.no_grad():
            output = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(output, dim=1)

        predicted_class = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][predicted_class].item()

        result = "Passed" if predicted_class == 1 else "Failed"
        filename = Path(image_path).name

        return {
            'filename': filename,
            'result': result,
            'confidence': confidence,
            'probabilities': probabilities[0].cpu().numpy(),
            'predicted_class': predicted_class
        }


def get_predictor(checkpoint_path, model_name='RETFound_mae', num_classes=2, input_size=224, device='cuda'):
    """Factory function to create a predictor instance."""
    return ModelPredictor(checkpoint_path, model_name, num_classes, input_size, device)