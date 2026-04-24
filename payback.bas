Function payback(Invest As Double, FCF As Range) As Variant
    Dim msgErro As String
    Dim i As Integer            'i é o contador
    Dim acFluxo As Double

    'somar os fluxos até cobrir o investimento

    If Invest >= 0 Then
        msgErro = "Investimento deve ser < 0 !"
        payback = msgErro
        Exit Function
    End If

    acFluxo = Invest              'começa negativo

    For i = 1 To FCF.Count
        acFluxo = acFluxo + FCF(i)

        If acFluxo >= 0 Then
            payback = i           'período em que o payback ocorre
            Exit Function
        End If
    Next i

    payback = "Payback não atingido"
End Function
