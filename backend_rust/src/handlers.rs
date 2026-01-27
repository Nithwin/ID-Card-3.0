
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Json},
};
use sqlx::{SqlitePool, query, query_as};
use crate::models::{LoginRequest, LoginResponse, RegisterRequest, User};
use crate::auth::{hash_password, verify_password, create_jwt};
use std::env;

pub async fn register(
    State(pool): State<SqlitePool>,
    Json(payload): Json<RegisterRequest>,
) -> impl IntoResponse {
    // Check if user exists
    let exists: Option<(String,)> = query_as("SELECT username FROM user WHERE username = ?")
        .bind(&payload.username)
        .fetch_optional(&pool)
        .await
        .unwrap_or(None);

    if exists.is_some() {
        return (StatusCode::BAD_REQUEST, "Username already exists").into_response();
    }

    // Hash Password
    let hashed = match hash_password(&payload.password) {
        Ok(h) => h,
        Err(_) => return (StatusCode::INTERNAL_SERVER_ERROR, "Hashing failed").into_response(),
    };

    // Insert
    let result = query("INSERT INTO user (username, hashed_password, role) VALUES (?, ?, ?)")
        .bind(&payload.username)
        .bind(hashed)
        .bind("user")
        .execute(&pool)
        .await;

    match result {
        Ok(_) => (StatusCode::CREATED, "User registered").into_response(),
        Err(e) => {
            println!("DB Error: {:?}", e);
            (StatusCode::INTERNAL_SERVER_ERROR, "Database error").into_response()
        }
    }
}

pub async fn login(
    State(pool): State<SqlitePool>,
    Json(payload): Json<LoginRequest>,
) -> impl IntoResponse {
    // Get User
    let user: Option<User> = query_as("SELECT * FROM user WHERE username = ?")
        .bind(&payload.username)
        .fetch_optional(&pool)
        .await
        .unwrap_or(None);

    let user = match user {
        Some(u) => u,
        None => return (StatusCode::UNAUTHORIZED, "Invalid credentials").into_response(),
    };

    // Verify Password
    if !verify_password(&payload.password, &user.hashed_password) {
        return (StatusCode::UNAUTHORIZED, "Invalid credentials").into_response();
    }

    // Generate Token
    let secret = env::var("JWT_SECRET").unwrap_or_else(|_| "secret".to_string());
    let token = match create_jwt(&user.username, &secret) {
        Ok(t) => t,
        Err(_) => return (StatusCode::INTERNAL_SERVER_ERROR, "Token generation failed").into_response(),
    };

    Json(LoginResponse {
        access_token: token,
        token_type: "Bearer".to_string(),
    }).into_response()
}

use axum::extract::Multipart;
use crate::AppState;

pub async fn detect(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> impl IntoResponse {
    while let Some(field) = multipart.next_field().await.unwrap() {
        if field.name() == Some("file") {
            let data = field.bytes().await.unwrap();
            
            match state.model.detect(&data) {
                Ok(detections) => return Json(serde_json::json!({
                    "detections": detections,
                    "count": detections.len()
                })).into_response(),
                Err(e) => {
                    println!("Inference Error: {:?}", e);
                    return (StatusCode::INTERNAL_SERVER_ERROR, "Detection failed").into_response()
                }
            }
        }
    }
    (StatusCode::BAD_REQUEST, "No file uploaded").into_response()
}
