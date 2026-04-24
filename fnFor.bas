Function fnFor(n As Integer) As Long
    Dim i As Integer
    Dim acumulador As Long

    acumulador = 0
    For i = 1 To n Step 1
        acumulador = acumulador + i
    Next i
    fnFor = acumulador
End Function
