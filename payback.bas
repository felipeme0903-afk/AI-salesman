Function payback(Invest As Double, FCF As Range) As Variant
    Dim i As Integer            'i é o contador
    Dim acFluxo As Double       'fluxo de caixa acumulado

    'Investimento precisa ser uma saída de caixa (negativo)
    If Invest >= 0 Then
        payback = "Investimento deve ser < 0 !"
        Exit Function
    End If

    acFluxo = Invest            'começa no negativo do investimento

    For i = 1 To FCF.Count
        acFluxo = acFluxo + FCF(i)
        If acFluxo >= 0 Then
            payback = i         'período em que o payback ocorre
            Exit Function
        End If
    Next i

    payback = "Payback não atingido"
End Function
