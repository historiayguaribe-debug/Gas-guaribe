# ... (código existente)

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/cargas", response_class=HTMLResponse)
async def admin_cargas(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_cargas.html", {"request": request})

@router.get("/ventas", response_class=HTMLResponse)
async def admin_ventas(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_ventas.html", {"request": request})

@router.get("/clientes", response_class=HTMLResponse)
async def admin_clientes(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_clientes.html", {"request": request})

@router.get("/reportes", response_class=HTMLResponse)
async def admin_reportes(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_reportes.html", {"request": request})

@router.get("/asistente", response_class=HTMLResponse)
async def admin_asistente(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_chat.html", {"request": request})
