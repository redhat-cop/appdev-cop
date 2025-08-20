package com.redhat.rhdg.demo.client.controller;

import org.infinispan.client.hotrod.Flag;
import org.infinispan.client.hotrod.RemoteCache;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

public abstract class Controller<K, V> {
	
	protected abstract RemoteCache<K, V> getCache();
	
	protected abstract K createKey(String uid);
	
	protected abstract V createValue(String value);

	@GetMapping(value = "/{uid}")
	public Object get(@PathVariable(name = "uid") String uid) {
		return getCache().get(createKey(uid));
	}

	@PostMapping(value = "/{uid}")
	public Object create(@PathVariable("uid") String uid, @RequestBody String value) {
		getCache().put(createKey(uid), createValue(value));
		return value;
	}

	@DeleteMapping(value = "/{uid}")
	public Object delete(@PathVariable("uid") String uid) {
		return getCache().withFlags(Flag.FORCE_RETURN_VALUE).remove(createKey(uid));
	}
}
