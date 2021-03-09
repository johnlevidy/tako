# tako output name, proto name
define tako_cpp_int
$${GENSRC_DIR}/$(1) $${GENSRC_DIR}/$(basename $(1))/json.hh $${GENSRC_DIR}/$(basename $(1))/core.hh:
	@mkdir -p $$(dir $$@)
	$${ON_TERSE} echo [TAKO-CPP] $(2)
	$${ON_VERBOSE} bin/tako generate takolsir $(2) lsir
	$${ON_VERBOSE} bin/tako generate ${GENSRC_DIR} $(2) cpp --json

remove_lsir_$(1):
	@${_RMRF} takolsir

clean_c: remove_lsir_$(1)
endef


define tako_cpp
$(eval $(call tako_cpp_int,$(1),$(2)))
endef

# tako proto name
define tako_python_int
python/takogen/.phantom/$(1): $(2)
	@echo [TAKO-PY] $(1)
	@bin/tako generate --namespace takogen python $(1) python
	@mkdir -p python/takogen/.phantom/
	@touch python/takogen/.phantom/$(1)

install_python: python/takogen/.phantom/$(1)

.PHONY: clean_python_$(1)
clean_python_$(1):
	@${_RMRF} python/takogen

clean_python: clean_python_$(1)

endef

define tako_python
$(eval $(call tako_python_int,$(1),$(2)))
endef
