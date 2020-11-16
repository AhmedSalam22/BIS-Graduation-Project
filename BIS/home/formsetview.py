from extra_views import FormSetView
from django.forms import formset_factory

class MyFormSetView(FormSetView):
    # هنا انا بغير بعد الدوال عن طريق مفهوم الوراثة علشان اقدر افلتر الفورم لكل مستخدم
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates a blank version of the formset.
        """
        
        formset = self.construct_formset(request) #overriding
        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a formset instance with the passed
        POST variables and then checked for validity.
        """
        formset = self.construct_formset(request)
        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)
    
    
    def construct_formset(self , request):
        """
        Returns an instance of the formset
        """
        formset_class = self.get_formset(request) #overriding
        if hasattr(self, "get_extra_form_kwargs"):
            klass = type(self).__name__
            raise DeprecationWarning(
                "Calling {0}.get_extra_form_kwargs is no longer supported. "
                "Set `form_kwargs` in {0}.formset_kwargs or override "
                "{0}.get_formset_kwargs() directly.".format(klass)
            )
        return formset_class(**self.get_formset_kwargs())

  
    def get_formset(self , request):
        """
        Returns the formset class from the formset factory
        """
        return formset_factory(self.get_form_class(request), **self.get_factory_kwargs()) #overriding

    
    def get_formset(self , request):
        """
        Returns the formset class from the formset factory
        """
        return formset_factory(self.get_form_class(request), **self.get_factory_kwargs()) #overriding