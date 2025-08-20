package com.redhat.rhdg.demo.client.controller;

import org.infinispan.client.hotrod.RemoteCache;
import org.infinispan.client.hotrod.RemoteCacheManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.redhat.rhdg.demo.model.serial.SerialKey;
import com.redhat.rhdg.demo.model.serial.SerialValue;

import jakarta.transaction.Transactional;

@RestController
@RequestMapping("/serial")
@Transactional
public class SerialController extends Controller<SerialKey, SerialValue> {

	private static final String CACHE_NAME = "serial-cache";

	@Autowired
	@Qualifier("serialRcm")
	RemoteCacheManager rcm;

	@Override
	protected RemoteCache<SerialKey, SerialValue> getCache() {
		return rcm.getCache(CACHE_NAME);
	}

	@Override
	protected SerialKey createKey(String uid) {
		return new SerialKey(uid);
	}

	@Override
	protected SerialValue createValue(String value) {
		return new SerialValue(value);
	}
}
