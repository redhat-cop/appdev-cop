package com.redhat.rhdg.demo.client.controller;

import java.util.Map;

import org.infinispan.client.hotrod.RemoteCache;
import org.infinispan.client.hotrod.RemoteCacheManager;
import org.infinispan.client.hotrod.Search;
import org.infinispan.query.dsl.Query;
import org.infinispan.query.dsl.QueryFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.redhat.rhdg.demo.model.proto.ProtoKey;
import com.redhat.rhdg.demo.model.proto.ProtoValue;

import jakarta.transaction.Transactional;

@RestController
@RequestMapping("/proto")
@Transactional
public class ProtoController extends Controller<ProtoKey, ProtoValue> {

	private static final String CACHE_NAME = "proto-cache";

	@Autowired
	@Qualifier("protoRcm")
	RemoteCacheManager rcm;

	@Override
	protected RemoteCache<ProtoKey, ProtoValue> getCache() {
		return rcm.getCache(CACHE_NAME);
	}

	@Override
	protected ProtoKey createKey(String uid) {
		return new ProtoKey(uid);
	}

	@Override
	protected ProtoValue createValue(String value) {
		return new ProtoValue(value);
	}

	@GetMapping(value = "/query/{queryText}")
	public Object[] query(@PathVariable("queryText") String queryText) {
		// Execute a full-text query
		QueryFactory queryFactory = Search.getQueryFactory(getCache());
		Query<ProtoValue> query = queryFactory.create("FROM rhdg_demo.ProtoValue WHERE data = :queryText");
		query.setParameter("queryText", queryText);
		return query.execute().list().toArray();
	}

	@PostMapping(value = "/removeTask/{uid}")
	public Object executeTask(@PathVariable("uid") String uid) {
		return getCache().execute("removeTask", Map.of("uid", uid));
	}
}
