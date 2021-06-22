import xlsxwriter

class ExportFSToExcel:
    def __init__(self, path, rowNum=7) -> None:
        self.path = path
        self.row = rowNum
        try:
            self.initialConfig()
            self.header()
        except Exception as e:
            print(e)
        finally:
            if self.workbook:
                self.closeFile()


    @property
    def Row(self):
        self.row += 1
        return self.row

    def initialConfig(self):
        self.workbook = xlsxwriter.Workbook(self.path)
        self.worksheet = self.workbook.add_worksheet()
        self.worksheet.set_column('A:A', 20)
        self.worksheet.set_column('B:B', 20)
        self.worksheet.set_column('C:C', 20)
    
    def header(self):
         # Add a bold format to use to highlight cells.
        bold = self.workbook.add_format({'bold': True})
        self.worksheet.write('A1', 'Business Information System', bold)
        self.worksheet.write('A2', 'Instructor Dr.Mona Ganna', bold)
        self.worksheet.write('A3', 'Student: Ahmed Maher Fouzy Mohamed Salam', bold)
        self.worksheet.write('A5' , "Trial Balance" , bold)
        self.worksheet.write('B6' , "Debit" , bold)
        self.worksheet.write('C6' , "Credit" , bold)

    def trialBalance(self, data):
        for  account_type , account , normal_balance , balance in data["data"]:
            self.worksheet.write(self.Row , 0 , account)
            if normal_balance == "Debit":
                self.worksheet.write(self.Row  , 1 , balance)
            else:
                self.worksheet.write(self.Row  , 2 , balance)

        self.worksheet.write(self.row , 0 , "Total")
        self.worksheet.write_formula(self.row , 1 , f"=sum(B7:B{self.row})")
        self.worksheet.write_formula(self.row , 2 , f"=sum(C7:C{self.row})")

    def incomeStatement(self):
        pass


    def ownersEquityStatement(self):
        pass



    def finacialStatement(self):
        pass


    def closeFile(self):
        self.workbook.close()
