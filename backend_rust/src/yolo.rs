
use image::{imageops::FilterType, GenericImageView};
use ort::{
    session::{Session, builder::GraphOptimizationLevel, builder::SessionBuilder},
    value::Value,
};
use anyhow::Result;
use std::sync::Mutex;

pub struct YoloModel {
    session: Mutex<Session>,
}

impl YoloModel {
    pub fn new(model_path: &str) -> Result<Self> {
        let session = SessionBuilder::new()?
            .with_optimization_level(GraphOptimizationLevel::Level3)?
            .with_intra_threads(4)?
            .commit_from_file(model_path)?;
        
        Ok(Self { session: Mutex::new(session) })
    }

    pub fn detect(&self, image_data: &[u8]) -> Result<Vec<Detection>> {
        // 1. Load Image
        let img = image::load_from_memory(image_data)?;
        
        // 2. Resize to 640x640
        let resized = img.resize_exact(640, 640, FilterType::Triangle);
        
        // 3. Prepare Data (Flat Vec in CHW format)
        // Efficient NCHW construction
        let mut red = Vec::with_capacity(640 * 640);
        let mut green = Vec::with_capacity(640 * 640);
        let mut blue = Vec::with_capacity(640 * 640);

        for (_x, _y, pixel) in resized.pixels() {
            red.push(pixel[0] as f32 / 255.0);
            green.push(pixel[1] as f32 / 255.0);
            blue.push(pixel[2] as f32 / 255.0);
        }
        
        let mut final_input = Vec::with_capacity(3 * 640 * 640);
        final_input.extend(red);
        final_input.extend(green);
        final_input.extend(blue);

        // 4. Create Tensor from (Shape, Data)
        let input_tensor = Value::from_array(([1, 3, 640, 640], final_input.into_boxed_slice()))?;
        
        // 5. Run Inference
        let mut session = self.session.lock().map_err(|_| anyhow::anyhow!("Session lock failed"))?;
        let _outputs = session.run(ort::inputs![input_tensor])?;
        
        // 6. Post-process (Placeholder)
        // let output = outputs["output0"].extract_tensor::<f32>()?;
        
        let mut detections = Vec::new();
        detections.push(Detection {
            x1: 0.1, y1: 0.1, x2: 0.5, y2: 0.5,
            score: 0.99,
            class_id: 1,
            class_name: "Person".to_string()
        });

        Ok(detections)
    }
}

#[derive(Debug, serde::Serialize)]
pub struct Detection {
    pub x1: f32,
    pub y1: f32,
    pub x2: f32,
    pub y2: f32,
    pub score: f32,
    pub class_id: usize,
    pub class_name: String,
}
