import pandas as pd
import numpy as np
import joblib
import os
from datetime import timedelta
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV

def preparar_datos(ventas):
    df = pd.DataFrame.from_records(
        ventas.values('fecha_venta', 'cantidad_vendida', 'precio_unitario')
    )
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
    df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce')
    df['precio_unitario']   = pd.to_numeric(df['precio_unitario'],   errors='coerce')
    df = df.groupby('fecha_venta').agg({
        'cantidad_vendida':'sum',
        'precio_unitario':'mean'
    }).reset_index()

    # Features temporales
    df['dias']       = (df['fecha_venta'] - df['fecha_venta'].min()).dt.days
    df['dia_semana'] = df['fecha_venta'].dt.dayofweek
    df['mes']        = df['fecha_venta'].dt.month

    # Lag, estacionalidades y móvil
    df['ventas_lag1'] = df['cantidad_vendida'].shift(1)
    df['sem_sin'] = np.sin(2*np.pi*df['dia_semana']/7)
    df['sem_cos'] = np.cos(2*np.pi*df['dia_semana']/7)
    df['mes_sin'] = np.sin(2*np.pi*(df['mes']-1)/12)
    df['mes_cos'] = np.cos(2*np.pi*(df['mes']-1)/12)
    df['prom_movil_7'] = df['cantidad_vendida'].rolling(window=7, min_periods=1).mean()

    # Rellenar nulos
    df = df.bfill().ffill()
    return df

def tune_hyperparameters(X, y):
    """
    Ajusta XGBRegressor con GridSearchCV y devuelve el mejor estimador.
    """
    base = XGBRegressor(use_label_encoder=False, verbosity=0, random_state=42)
    param_grid = {
        'n_estimators':    [100, 200],
        'max_depth':       [3, 5],
        'learning_rate':   [0.01, 0.05],
        'subsample':       [0.7, 1.0],
        'colsample_bytree':[0.7, 1.0]
    }
    grid = GridSearchCV(
        estimator=base,
        param_grid=param_grid,
        cv=3,
        scoring='neg_mean_squared_error',
        n_jobs=-1,
        verbose=0
    )
    grid.fit(X, y)
    return grid.best_estimator_

def entrenar_modelo(X, y, modelo_base=None):
    """
    Si recibe modelo_base (un XGBRegressor ya ajustado via tune_hyperparameters),
    lo entrena de nuevo; si no, crea uno por defecto.
    """
    if modelo_base is None:
        modelo = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            random_state=42
        )
    else:
        modelo = modelo_base
    modelo.fit(X, y)
    return modelo

def evaluar_modelo(model, X, y):
    neg_mse = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
    rmse_cv = np.sqrt(-neg_mse.mean())
    r2_cv = cross_val_score(model, X, y, cv=5, scoring='r2').mean()
    return rmse_cv, r2_cv

def predecir_proximos_dias(model, df, dias_futuros=7):
    ult_fecha = df['fecha_venta'].max()
    ult_dia   = df['dias'].max()
    fechas = [ult_fecha + timedelta(days=i) for i in range(1, dias_futuros+1)]
    futuros = pd.DataFrame({
        'dias':       [ult_dia+i for i in range(1, dias_futuros+1)],
        'dia_semana': [(ult_fecha+timedelta(days=i)).weekday() for i in range(1, dias_futuros+1)],
        'mes':        [(ult_fecha+timedelta(days=i)).month   for i in range(1, dias_futuros+1)],
        'ventas_lag1':[df['cantidad_vendida'].iloc[-1]]*dias_futuros,
        'sem_sin':    [np.sin(2*np.pi*((ult_fecha+timedelta(days=i)).weekday())/7) for i in range(1, dias_futuros+1)],
        'sem_cos':    [np.cos(2*np.pi*((ult_fecha+timedelta(days=i)).weekday())/7) for i in range(1, dias_futuros+1)],
        'mes_sin':    [np.sin(2*np.pi*(((ult_fecha+timedelta(days=i)).month-1)/12)) for i in range(1, dias_futuros+1)],
        'mes_cos':    [np.cos(2*np.pi*(((ult_fecha+timedelta(days=i)).month-1)/12)) for i in range(1, dias_futuros+1)],
        'prom_movil_7':[df['cantidad_vendida'].tail(7).mean()]*dias_futuros,
        'precio_unitario':[df['precio_unitario'].iloc[-1]]*dias_futuros
    })
    preds = model.predict(futuros)
    return fechas, preds

def guardar_modelo(model, ruta='media/modelo_xgb.pkl'):
    joblib.dump(model, ruta)

def cargar_modelo(ruta='media/modelo_xgb.pkl'):
    if os.path.exists(ruta):
        return joblib.load(ruta)
    return None
