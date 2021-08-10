# from multi_form_view import MultiFormView
# import six
# #ovride some method in MultiFormView To enable filter by current loign user
# class MyMultiFormView(MultiFormView):
#     def get(self, request,  *args, **kwargs):
#         """
#         Handles GET requests and instantiates blank versions of the forms.
#         """
#         return self.render_to_response(self.get_context_data(request))


#     def get_context_data(self,request, **kwargs):
#             """
#             Add forms into the context dictionary.
#             """
#             context = {}
#             if 'forms' not in kwargs:
#                 context['forms'] = self.get_forms(request)
#             else:
#                 context['forms'] = kwargs['forms']
#             return context

#     def get_forms(self , request):
#         """
#         Initializes the forms defined in `form_classes` with initial data from `get_initial()` and
#         kwargs from get_form_kwargs().
#         """
#         forms = {}
#         initial = self.get_initial()
#         form_kwargs = self.get_form_kwargs()
#         for key, form_class in six.iteritems(self.form_classes):
#             forms[key] = form_class(initial=initial[key], **form_kwargs[key])
#         return forms



    
#     def post(self, request, **kwargs):
#         """
#         Uses `are_forms_valid()` to call either `forms_valid()` or * `forms_invalid()`.
#         """
#         forms = self.get_forms(request)
#         if self.are_forms_valid(forms):
#             return self.forms_valid(forms)
#         else:
#             return self.forms_invalid(forms)