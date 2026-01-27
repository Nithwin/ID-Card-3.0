
mod models;
mod auth;
mod handlers;
mod yolo;

use axum::{
    routing::{get, post},
    Router,
    response::Json,
    extract::FromRef,
};
use std::net::SocketAddr;
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use dotenvy::dotenv;
use std::env;
use tower_http::cors::CorsLayer;
use handlers::{register, login, detect};
use std::sync::Arc;
use yolo::YoloModel;

#[derive(Clone)]
pub struct AppState {
    pub db: SqlitePool,
    pub model: Arc<YoloModel>,
}

impl FromRef<AppState> for SqlitePool {
    fn from_ref(state: &AppState) -> Self {
        state.db.clone()
    }
}

#[tokio::main]
async fn main() {
    // Load .env
    dotenv().ok();
    tracing_subscriber::fmt::init();

    // DB Setup
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let pool = SqlitePoolOptions::new()
        .connect(&database_url)
        .await
        .expect("Failed to connect to DB");

    println!("Connected to DB: {}", database_url);

    // AI Setup
    println!("Loading YOLO Model...");
    // Check if model exists, if not, wait or warn?
    // Assuming idcard.onnx is in CWD (backend_rust/)
    let model = Arc::new(YoloModel::new("idcard.onnx").expect("Failed to load ONNX model. Run export_onnx.py first!"));
    println!("YOLO Model Loaded.");

    let state = AppState {
        db: pool,
        model,
    };

    // App Router
    let app = Router::new()
        .route("/", get(root))
        .route("/register", post(register))
        .route("/token", post(login))
        .route("/detect", post(detect))
        .layer(CorsLayer::permissive())
        .with_state(state);

    // Run Server
    let addr = SocketAddr::from(([0, 0, 0, 0], 8082)); 
    println!("Rust Backend listening on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn root() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "Online",
        "service": "ID Card Rust Backend",
        "port": 8082
    }))
}
