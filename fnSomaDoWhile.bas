Function fnSomaDoWhile(tabela As Range) As Double 'as range pega uma área'
    Dim resultado As Double 'retorno da função
    Dim i As Integer 'índice

    'somar o conteúdo de todas as células'

    i = 1
    While i <= tabela.Count
        resultado = resultado + tabela(i)
        i = i + 1
    Wend

    fnSomaDoWhile = resultado

End Function
